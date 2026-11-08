/**
 * 学習記録（ブラウザの localStorage に保存）。
 * 端末・ブラウザごとの記録で、サーバーには送られない。
 */
export interface RecordEntry {
	/** 解答回数 */
	a: number;
	/** 正解回数 */
	c: number;
	/** 直近の解答が正解だったか */
	last: boolean;
	/** 直近の解答日時（ms） */
	t: number;
}

export type RecordMap = Record<string, RecordEntry>;

const KEY = 'kangyo-record-v1';

export function loadRecord(): RecordMap {
	try {
		const raw = localStorage.getItem(KEY);
		return raw ? (JSON.parse(raw) as RecordMap) : {};
	} catch {
		return {};
	}
}

export function saveRecord(map: RecordMap) {
	try {
		localStorage.setItem(KEY, JSON.stringify(map));
	} catch {
		/* プライベートモードなどで保存できない場合は何もしない */
	}
}

export function addResult(id: string, correct: boolean) {
	const map = loadRecord();
	const e = map[id] ?? { a: 0, c: 0, last: false, t: 0 };
	e.a += 1;
	if (correct) e.c += 1;
	e.last = correct;
	e.t = Date.now();
	map[id] = e;
	saveRecord(map);
}

export function clearRecord() {
	try {
		localStorage.removeItem(KEY);
	} catch {
		/* noop */
	}
}

export const RECORD_KEY = KEY;
