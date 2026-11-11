// mystudio 업로드 실행기 — GitHub Actions(mystudio-upload.yml)에서 돈다. Node 20+, 추가 설치 없음.
// mystudio-media 브랜치의 mystudio/jobs/*.json 을 읽어, 때가 된 작업을 인스타·유튜브에 게시하고 결과를 적어 둔다.
//
// 작업 종류
//   ig_carousel : 사진(JPEG) 1~10장 → 캐러셀(1장이면 단일 사진)
//   ig_reel     : mp4 → 릴스
//   yt          : mp4 → 유튜브 (예약이면 유튜브의 예약 공개 기능을 쓴다)
//   check       : 연결된 계정 이름 확인
//
// 비밀값: IG_ACCESS_TOKEN[_X], IG_USER_ID[_X], YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN[_X]
import fs from 'node:fs';
import path from 'node:path';

const REPO = process.env.GITHUB_REPOSITORY;          // owner/name
const BRANCH = 'mystudio-media';
const RAW = `https://raw.githubusercontent.com/${REPO}/${BRANCH}/`;
const JOBS = 'mystudio/jobs';
const IG = 'https://graph.instagram.com/v25.0';
const sleep = ms => new Promise(r => setTimeout(r, ms));
const now = () => new Date();
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const sfx = s => (s ? '_' + String(s).toUpperCase() : '');

// ── 인스타 ─────────────────────────────────────────
function igCreds(account) {
  const token = process.env['IG_ACCESS_TOKEN' + sfx(account)], user = process.env['IG_USER_ID' + sfx(account)];
  if (!token || !user) throw new Error(`이 저장소에 인스타 비밀값 IG_ACCESS_TOKEN${sfx(account)} / IG_USER_ID${sfx(account)} 이 없습니다`);
  return { token, user };
}
async function ig(c, method, p, params = {}) {
  const url = new URL(`${IG}/${p}`);
  const opt = { method, headers: { Authorization: `Bearer ${c.token}` } };
  if (method === 'GET') Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
  else { opt.headers['Content-Type'] = 'application/json'; opt.body = JSON.stringify(params); }
  const r = await fetch(url, opt); const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error(`인스타 API 오류 ${r.status}: ${JSON.stringify(j.error || j).slice(0, 400)}`);
  return j;
}
async function igWait(c, id, tries = 20) {
  for (let i = 0; i < tries; i++) {
    const st = (await ig(c, 'GET', id, { fields: 'status_code' })).status_code;
    if (st === 'FINISHED') return;
    if (st === 'ERROR' || st === 'EXPIRED') throw new Error(`인스타가 미디어 처리에 실패했습니다 (${st})`);
    await sleep(15000);
  }
  throw new Error('인스타 미디어 준비 시간 초과');
}
// 게시 응답이 오류여도 실제로는 올라갔을 수 있다 → 다시 보내기 전에 최근 게시물에서 같은 캡션을 찾는다
async function igAlready(c, caption) {
  try {
    const recent = (await ig(c, 'GET', `${c.user}/media`, { fields: 'id,caption', limit: 10 })).data || [];
    const head = (caption || '').slice(0, 80);
    return head ? recent.find(m => (m.caption || '').slice(0, 80) === head)?.id : null;
  } catch { return null; }
}
async function igPublish(c, creation, caption) {
  for (let k = 0; k < 6; k++) {
    try { return (await ig(c, 'POST', `${c.user}/media_publish`, { creation_id: creation })).id; }
    catch (e) {
      await sleep(15000);
      const done = await igAlready(c, caption);
      if (done) { log('게시 응답은 오류였지만 이미 올라가 있어 다시 보내지 않음', done); return done; }
      if (!String(e.message).includes('2207027') || k === 5) throw e;
    }
  }
}
async function igLink(c, id) { try { return (await ig(c, 'GET', id, { fields: 'permalink' })).permalink || ''; } catch { return ''; } }

async function igCarousel(job) {
  const c = igCreds(job.account); const caption = (job.caption || '').slice(0, 2200);
  const urls = job.media.map(m => RAW + m);
  let creation;
  if (urls.length === 1) {
    creation = (await ig(c, 'POST', `${c.user}/media`, { image_url: urls[0], caption })).id;
    await igWait(c, creation);
  } else {
    const kids = [];
    for (const u of urls.slice(0, 10)) kids.push((await ig(c, 'POST', `${c.user}/media`, u.endsWith('.mp4') ? { media_type: 'VIDEO', video_url: u, is_carousel_item: true } : { image_url: u, is_carousel_item: true })).id);
    for (const k of kids) await igWait(c, k);
    creation = (await ig(c, 'POST', `${c.user}/media`, { media_type: 'CAROUSEL', children: kids.join(','), caption })).id;
    await igWait(c, creation);
  }
  await sleep(8000);
  const id = await igPublish(c, creation, caption);
  return { id, url: await igLink(c, id) };
}
async function igReel(job) {
  const c = igCreds(job.account); const caption = (job.caption || '').slice(0, 2200);
  const extra = job.cover ? { cover_url: RAW + job.cover } : {};
  const creation = (await ig(c, 'POST', `${c.user}/media`, { media_type: 'REELS', video_url: RAW + job.media[0], caption, share_to_feed: !!job.share_to_feed, ...extra })).id;
  await igWait(c, creation, 40);
  const id = await igPublish(c, creation, caption);
  return { id, url: await igLink(c, id) };
}

// ── 유튜브 ─────────────────────────────────────────
async function ytToken(channel) {
  const rt = process.env['YT_REFRESH_TOKEN' + sfx(channel)];
  if (!rt || !process.env.YT_CLIENT_ID) throw new Error(`이 저장소에 유튜브 비밀값 YT_REFRESH_TOKEN${sfx(channel)} 이 없습니다`);
  const r = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', body: new URLSearchParams({
    client_id: process.env.YT_CLIENT_ID, client_secret: process.env.YT_CLIENT_SECRET, refresh_token: rt, grant_type: 'refresh_token' }) });
  const j = await r.json();
  if (!j.access_token) throw new Error('유튜브 로그인 갱신 실패: ' + JSON.stringify(j).slice(0, 200));
  return j.access_token;
}
async function ytUpload(job) {
  const y = job.yt || {}; const token = await ytToken(job.channel);
  const status = { privacyStatus: y.privacy || 'public', selfDeclaredMadeForKids: false, containsSyntheticMedia: !!y.synthetic };
  const at = job.publish_at ? new Date(job.publish_at) : null;
  if (at && at - now() > 10 * 60000) Object.assign(status, { privacyStatus: 'private', publishAt: at.toISOString() });
  const meta = { snippet: { title: (y.title || '제목 없음').slice(0, 100), description: (y.description || '').slice(0, 4900), tags: (y.tags || []).slice(0, 15),
    categoryId: String(y.category || 22), defaultLanguage: 'ko', defaultAudioLanguage: 'ko' }, status };
  const video = Buffer.from(await (await fetch(RAW + job.media[0])).arrayBuffer());
  const init = await fetch('https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status', {
    method: 'POST', body: JSON.stringify(meta),
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json; charset=UTF-8', 'X-Upload-Content-Type': 'video/mp4', 'X-Upload-Content-Length': String(video.length) } });
  if (!init.ok) throw new Error(`유튜브 업로드 시작 실패 ${init.status}: ${(await init.text()).slice(0, 300)}`);
  const put = await fetch(init.headers.get('location'), { method: 'PUT', body: video, headers: { 'Content-Type': 'video/mp4' } });
  const j = await put.json().catch(() => ({}));
  if (!put.ok || !j.id) throw new Error(`유튜브 업로드 실패 ${put.status}: ${JSON.stringify(j).slice(0, 300)}`);
  if (job.thumb) {
    const img = Buffer.from(await (await fetch(RAW + job.thumb)).arrayBuffer());
    await fetch(`https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=${j.id}&uploadType=media`, { method: 'POST', body: img, headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'image/jpeg' } }).catch(() => {});
  }
  const shorts = (y.shorts ?? true) ? `https://youtube.com/shorts/${j.id}` : `https://youtu.be/${j.id}`;
  return { id: j.id, url: shorts, privacy: j.status?.privacyStatus, publishAt: j.status?.publishAt || null };
}

// ── 계정 확인 ───────────────────────────────────────
async function check() {
  const out = { instagram: [], youtube: [] };
  for (const k of Object.keys(process.env).filter(k => /^IG_ACCESS_TOKEN(_\w+)?$/.test(k) && process.env[k])) {
    const acct = k.replace('IG_ACCESS_TOKEN', '').replace(/^_/, '').toLowerCase();
    try { const c = igCreds(acct); const me = await ig(c, 'GET', 'me', { fields: 'username' }); out.instagram.push({ account: acct, username: me.username }); }
    catch (e) { out.instagram.push({ account: acct, error: e.message.slice(0, 200) }); }
  }
  for (const k of Object.keys(process.env).filter(k => /^YT_REFRESH_TOKEN(_\w+)?$/.test(k) && process.env[k])) {
    const ch = k.replace('YT_REFRESH_TOKEN', '').replace(/^_/, '').toLowerCase();
    try {
      const t = await ytToken(ch);
      const j = await (await fetch('https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true', { headers: { Authorization: `Bearer ${t}` } })).json();
      out.youtube.push({ channel: ch, title: j.items?.[0]?.snippet?.title || '(채널 없음)', id: j.items?.[0]?.id });
    } catch (e) { out.youtube.push({ channel: ch, error: e.message.slice(0, 200) }); }
  }
  return out;
}

// ── 실행 ───────────────────────────────────────────
const RUNNERS = { ig_carousel: igCarousel, ig_reel: igReel, yt: ytUpload, check };
const files = fs.existsSync(JOBS) ? fs.readdirSync(JOBS).filter(f => f.endsWith('.json')) : [];
let changed = 0; const toDelete = [];
for (const f of files.sort()) {
  const p = path.join(JOBS, f); const job = JSON.parse(fs.readFileSync(p, 'utf8'));
  if (job.status !== 'queued') continue;
  // 유튜브는 예약 시각을 유튜브가 지키므로 바로 올린다. 인스타는 시각이 돼야 올린다.
  const due = job.type === 'yt' || job.type === 'check' || !job.publish_at || new Date(job.publish_at) <= now();
  if (!due) continue;
  log('작업 시작', job.id, job.type);
  job.attempts = (job.attempts || 0) + 1;
  try {
    job.result = await RUNNERS[job.type](job);
    job.status = 'done'; job.error = null; job.done_at = now().toISOString();
    log('완료', job.id, JSON.stringify(job.result).slice(0, 300));
    if (job.type !== 'check') toDelete.push(...(job.media || []), ...(job.cover ? [job.cover] : []), ...(job.thumb ? [job.thumb] : []));
  } catch (e) {
    job.error = String(e.message || e).slice(0, 800);
    // 일시적인 문제일 수 있으니 3번까지 다음 실행에서 다시 시도
    job.status = job.attempts >= 3 ? 'error' : 'queued';
    log('실패', job.id, job.error);
  }
  job.updated_at = now().toISOString();
  fs.writeFileSync(p, JSON.stringify(job, null, 2)); changed++;
}
// 게시가 끝난 파일은 브랜치에서 지워 저장소가 커지지 않게 한다
for (const m of toDelete) { try { fs.rmSync(m, { force: true }); } catch {} }
console.log(`처리한 작업 ${changed}개`);
