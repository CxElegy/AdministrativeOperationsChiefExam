/**
 * 学習記録（ブラウザの localStorage に保存。「進度リンク」を使うときは sync.ts が自分の進度サーバーにも送る）
 *
 * - 問題ごとの成績と「メモ帳（復習）」の予定
 * - 部屋ごとのクリア状況
 * - 日ごとの解答数（連続学習日数・今日の目標に使う）
 * - 総会（模試）の結果
 */
export interface QRec {
	/** 解答回数 */
	a: number;
	/** 正解回数 */
	c: number;
	/** 直近の解答が正解か */
	last: boolean;
	/** 直近の解答日時 */
	t: number;
	/** メモ帳の段階（0 = 間違えたばかり）。未定義ならメモ帳に入っていない */
	box?: number;
	/** 次にメモ帳に出てくる日時 */
	due?: number;
}

export interface RoomRec {
	/** 最高正解数 */
	best: number;
	total: number;
	t: number;
}

export interface ExamRec {
	exam: string;
	label: string;
	score: number;
	total: number;
	passMark: number | null;
	t: number;
}

export interface Store {
	v: 1;
	q: Record<string, QRec>;
	rooms: Record<string, RoomRec>;
	days: Record<string, number>;
	exams: ExamRec[];
}

const KEY = 'kangyo-mansion-v1';
const DAY = 86_400_000;
/** メモ帳で正解したとき、次に出すまでの日数（段階ごと） */
const INTERVALS = [1, 3, 7, 14, 30];
/** この段階まで正解し続けたらメモ帳を卒業 */
export const GRADUATE = INTERVALS.length;
export const DAILY_GOAL = 10;

const empty = (): Store => ({ v: 1, q: {}, rooms: {}, days: {}, exams: [] });

export function load(): Store {
	try {
		const raw = localStorage.getItem(KEY);
		if (!raw) return empty();
		const s = JSON.parse(raw);
		return { ...empty(), ...s };
	} catch {
		return empty();
	}
}

let onSave: ((s: Store) => void) | null = null;
/** 保存のたびに呼ぶ（進度サーバーへの送信用） */
export function setOnSave(f: ((s: Store) => void) | null) {
	onSave = f;
}

export function save(s: Store) {
	onSave?.(s);
	try {
		localStorage.setItem(KEY, JSON.stringify(s));
	} catch {
		/* 保存できない環境（プライベートモードなど）では記録しない */
	}
}

export const dayKey = (t = Date.now()) => {
	const d = new Date(t);
	return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

/** 1問の解答を記録する */
export function recordAnswer(s: Store, id: string, ok: boolean) {
	const now = Date.now();
	const r = s.q[id] ?? { a: 0, c: 0, last: false, t: 0 };
	r.a += 1;
	if (ok) r.c += 1;
	r.last = ok;
	r.t = now;
	if (!ok) {
		// 間違えたらメモ帳へ（すぐに復習できる）
		r.box = 0;
		r.due = now;
	} else if (r.box !== undefined) {
		r.box += 1;
		r.due = r.box >= GRADUATE ? undefined : now + INTERVALS[r.box - 1] * DAY;
		if (r.box >= GRADUATE) delete r.box;
	}
	s.q[id] = r;
	const k = dayKey(now);
	s.days[k] = (s.days[k] ?? 0) + 1;
}

export function recordRoom(s: Store, roomId: string, correct: number, total: number) {
	const prev = s.rooms[roomId];
	s.rooms[roomId] = { best: Math.max(prev?.best ?? 0, correct), total, t: Date.now() };
}

/** メモ帳で今日出す問題 */
export function dueIds(s: Store): string[] {
	const now = Date.now();
	return Object.entries(s.q)
		.filter(([, r]) => r.box !== undefined && (r.due ?? 0) <= now)
		.sort((a, b) => (a[1].due ?? 0) - (b[1].due ?? 0))
		.map(([id]) => id);
}

/** メモ帳に入っているが、まだ日が来ていない問題の数 */
export function waitingCount(s: Store): number {
	const now = Date.now();
	return Object.values(s.q).filter((r) => r.box !== undefined && (r.due ?? 0) > now).length;
}

/** 連続学習日数（今日まだ解いていなければ昨日までで数える） */
export function streak(s: Store): number {
	let n = 0;
	let t = Date.now();
	if (!s.days[dayKey(t)]) t -= DAY;
	while (s.days[dayKey(t)]) {
		n += 1;
		t -= DAY;
	}
	return n;
}

export const todayCount = (s: Store) => s.days[dayKey()] ?? 0;

export function exportJson(s: Store) {
	return JSON.stringify(s);
}

export function importJson(text: string): Store {
	const data = JSON.parse(text);
	if (!data || typeof data !== 'object' || !data.q) throw new Error('invalid');
	return { ...empty(), ...data };
}

export function clear() {
	try {
		localStorage.removeItem(KEY);
	} catch {
		/* noop */
	}
}
