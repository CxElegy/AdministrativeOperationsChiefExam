/**
 * 「進度リンク」：リンクに入っている ID ごとに、自分のパソコンの進度サーバーへ記録を保存する。
 *
 *   https://…/AdministrativeOperationsChiefExam/?u=<ID>&api=<進度サーバーのURL>
 *
 * - u と api は最初に開いたときにこのブラウザに覚える（以後はリンクなしで開いても同じ記録）
 * - 進度サーバーからこのサイトを開いた場合（同じ Wi-Fi のスマホなど）は api を書かなくてよい
 * - サーバーに届かないときはこれまで通りブラウザの中だけに保存し、届いたときに合わせる
 */
import { dayKey, type Store } from './store';

const CFG_KEY = 'kangyo-sync-v1';
export interface SyncConfig {
	id: string;
	api: string;
}
export type SyncState = 'off' | 'syncing' | 'ok' | 'error';

const ID_RE = /^[A-Za-z0-9_-]{12,64}$/;

function readCfg(): Partial<SyncConfig> {
	try {
		return JSON.parse(localStorage.getItem(CFG_KEY) || '{}');
	} catch {
		return {};
	}
}
function writeCfg(c: Partial<SyncConfig>) {
	try {
		localStorage.setItem(CFG_KEY, JSON.stringify(c));
	} catch {
		/* noop */
	}
}

/** URL の ?u= / ?api= を読み、保存済みの設定と合わせる */
export function syncConfig(): SyncConfig | null {
	const cfg = readCfg();
	const p = new URLSearchParams(location.search);
	const u = p.get('u');
	const api = p.get('api');
	if (u && ID_RE.test(u)) cfg.id = u;
	if (api) cfg.api = api.replace(/\/+$/, '');
	if (u || api) writeCfg(cfg);
	// 進度サーバーそのものから開いているときは同じ場所の /api を使う
	const sameOrigin = location.protocol.startsWith('http') && !location.hostname.endsWith('github.io') && location.port !== '4321' ? location.origin : '';
	const base = cfg.api || sameOrigin;
	return cfg.id && base ? { id: cfg.id, api: base } : null;
}

export function newId() {
	const b = new Uint8Array(12);
	crypto.getRandomValues(b);
	return Array.from(b, (x) => 'abcdefghijkmnpqrstuvwxyz23456789'[x % 32]).join('') + Date.now().toString(36).slice(-4);
}

export function setConfig(c: Partial<SyncConfig>) {
	writeCfg({ ...readCfg(), ...c });
}
export function clearConfig() {
	writeCfg({});
}
export const savedConfig = readCfg;

/** この設定で開ける「進度リンク」 */
export function shareLink(cfg: SyncConfig, base = location.origin + location.pathname.replace(/[^/]*$/, '')) {
	const sameOrigin = cfg.api === location.origin;
	return `${base}?u=${encodeURIComponent(cfg.id)}${sameOrigin ? '' : `&api=${encodeURIComponent(cfg.api)}`}`;
}

export async function pull(cfg: SyncConfig): Promise<{ main?: Store; william?: unknown } | null> {
	const r = await fetch(`${cfg.api}/api/progress/${cfg.id}`, { cache: 'no-store' });
	if (r.status === 404) return null;
	if (!r.ok) throw new Error(`HTTP ${r.status}`);
	return (await r.json()).data ?? null;
}

export async function push(cfg: SyncConfig, data: { main?: Store; william?: unknown }) {
	const r = await fetch(`${cfg.api}/api/progress/${cfg.id}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ data }),
	});
	if (!r.ok) throw new Error(`HTTP ${r.status}`);
}

/** 2つの記録を合わせる（どちらの端末で解いた分も残す） */
export function mergeStore(a: Store, b: Store): Store {
	// どちらかでリセットされていたら、その日時より前の記録は捨てる
	const reset = Math.max(a.reset ?? 0, b.reset ?? 0);
	if (reset) {
		const cut = (s: Store): Store => ({
			v: 1,
			q: Object.fromEntries(Object.entries(s.q ?? {}).filter(([, r]) => r.t >= reset)),
			rooms: Object.fromEntries(Object.entries(s.rooms ?? {}).filter(([, r]) => r.t >= reset)),
			days: Object.fromEntries(Object.entries(s.days ?? {}).filter(([d]) => d > dayKey(reset))),
			exams: (s.exams ?? []).filter((e) => e.t >= reset),
		});
		if ((a.reset ?? 0) < reset) a = cut(a);
		if ((b.reset ?? 0) < reset) b = cut(b);
	}
	const out: Store = { v: 1, q: { ...a.q }, rooms: { ...a.rooms }, days: { ...a.days }, exams: [] };
	if (reset) out.reset = reset;
	for (const [id, r] of Object.entries(b.q ?? {})) {
		const x = out.q[id];
		out.q[id] = !x || r.t > x.t ? { ...r, a: Math.max(r.a, x?.a ?? 0), c: Math.max(r.c, x?.c ?? 0) } : { ...x, a: Math.max(r.a, x.a), c: Math.max(r.c, x.c) };
	}
	for (const [id, r] of Object.entries(b.rooms ?? {})) {
		const x = out.rooms[id];
		out.rooms[id] = !x ? r : { best: Math.max(x.best, r.best), total: r.total, t: Math.max(x.t, r.t) };
	}
	for (const [d, n] of Object.entries(b.days ?? {})) out.days[d] = Math.max(out.days[d] ?? 0, n);
	const seen = new Set<string>();
	for (const e of [...(a.exams ?? []), ...(b.exams ?? [])]) {
		const k = `${e.exam}-${e.t}`;
		if (!seen.has(k)) {
			seen.add(k);
			out.exams.push(e);
		}
	}
	out.exams.sort((x, y) => x.t - y.t);
	return out;
}
