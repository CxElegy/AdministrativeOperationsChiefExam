/**
 * マンション攻略 — 画面の動き
 *
 * 左：マンション（階＝分野、窓＝部屋＝5問のレッスン）と管理人さんのひとこと
 * 右：ホーム／部屋（レッスン）／メモ帳（復習）／総会（模試）／記録
 *
 * 画面の切り替えは URL の # で行う（#/room/kubun-2, #/memo, #/soukai/r07 など）。
 */
import { CATEGORIES } from '../data/categories';
import * as S from './store';
import type { AppData, Exam, Floor, QItem, Room } from './types';

/* ---------- 小さな道具 ---------- */

const esc = (s: unknown) =>
	String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);
/** 解説用のごく簡単な記法: 改行 / **太字** */
const rich = (s: string) => esc(s).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
const pick = <T,>(arr: T[], seed: number) => arr[Math.abs(seed) % arr.length];
const hash = (s: string) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) | 0, 7);
const catShort = (id: string) => CATEGORIES.find((c) => c.id === id)?.short ?? id;
const choiceMark = (q: QItem, i: number) =>
	q.choices.length === 2 && /正し|誤り/.test(q.choices.join('')) ? (i === 0 ? '○' : '×') : String(i + 1);

const PRAISE = ['そのとおり！', 'さすが！', 'いい調子！', '完璧だね！', 'よく覚えてたね！'];
const OOPS = ['おっと、惜しい！', 'ここは引っかかりやすいんだ', '大丈夫、ここで覚えよう', 'うーん、ちょっと違うんだ'];

/* ---------- イラスト ---------- */

function residentSvg(seed: string, size = 64) {
	const h = hash(seed);
	const shirts = ['#FF9F80', '#7FB3D5', '#9BD3AE', '#F4C06A', '#C3A6E0', '#F2A7C3'];
	const hairs = ['#6B4A2E', '#2A2622', '#8C5A3C', '#4A3B33', '#A7703F'];
	const shirt = pick(shirts, h);
	const hair = pick(hairs, h >> 3);
	const longHair = (h >> 5) & 1;
	return `<svg width="${size}" height="${Math.round(size * 1.2)}" viewBox="0 0 70 84" aria-hidden="true" class="avatar">
		<rect x="12" y="46" width="46" height="38" rx="16" fill="${shirt}"></rect>
		${longHair ? `<rect x="15" y="22" width="40" height="30" rx="12" fill="${hair}"></rect>` : ''}
		<circle cx="35" cy="30" r="19" fill="#F6D2B0"></circle>
		<path d="M16 28q4-18 19-18t19 18q-6-8-19-8t-19 8z" fill="${hair}"></path>
		<circle cx="28" cy="32" r="2.6" fill="#2A2622"></circle>
		<circle cx="42" cy="32" r="2.6" fill="#2A2622"></circle>
		<path d="M30 41q5 3 10 0" fill="none" stroke="#2A2622" stroke-width="2.2" stroke-linecap="round"></path>
	</svg>`;
}

function keeperSvg(size = 72, mood: 'smile' | 'happy' | 'think' = 'smile') {
	const mouth =
		mood === 'happy'
			? '<path d="M30 45q8 8 16 0z" fill="#2A2622"></path>'
			: mood === 'think'
				? '<path d="M32 47h12" stroke="#2A2622" stroke-width="2.4" stroke-linecap="round"></path>'
				: '<path d="M32 46q6 5 12 0" fill="none" stroke="#2A2622" stroke-width="2.4" stroke-linecap="round"></path>';
	return `<svg width="${size}" height="${Math.round(size * 1.26)}" viewBox="0 0 76 96" role="img" aria-label="管理人さん" class="avatar">
		<rect x="16" y="52" width="44" height="44" rx="14" fill="#4D6A9C"></rect>
		<rect x="33" y="56" width="10" height="14" rx="2" fill="#FFC857"></rect>
		<circle cx="38" cy="36" r="20" fill="#F6D2B0"></circle>
		<path d="M16 30q22-20 44 0v-4q-22-14-44 0z" fill="#2B3858"></path>
		<rect x="14" y="26" width="48" height="6" rx="3" fill="#2B3858"></rect>
		<circle cx="31" cy="38" r="2.6" fill="#2A2622"></circle>
		<circle cx="45" cy="38" r="2.6" fill="#2A2622"></circle>
		${mouth}
	</svg>`;
}

const keySvg = (size = 20) =>
	`<svg width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true"><circle cx="8" cy="12" r="5" fill="none" stroke="#C98A00" stroke-width="2.6"></circle><path d="M13 12h9M19 12v4M16 12v3" stroke="#C98A00" stroke-width="2.6" stroke-linecap="round"></path></svg>`;
const flameSvg = (size = 20) =>
	`<svg width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c1 4 6 6 6 12a6 6 0 0 1-12 0c0-3 2-5 3-6 0 2 1 3 2 3 0-4-1-6 1-9z" fill="#FF7A59"></path></svg>`;
const okSvg = `<svg width="20" height="20" viewBox="0 0 24 24" role="img" aria-label="正解"><circle cx="12" cy="12" r="10" fill="#2E9E6A"></circle><path d="M7.5 12l3 3 6-6" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"></path></svg>`;
const ngSvg = `<svg width="20" height="20" viewBox="0 0 24 24" role="img" aria-label="不正解"><circle cx="12" cy="12" r="10" fill="#C4482A"></circle><path d="M8.5 8.5l7 7M15.5 8.5l-7 7" stroke="#fff" stroke-width="2.4" stroke-linecap="round"></path></svg>`;

/* ---------- 画面の状態 ---------- */

type Lesson = {
	kind: 'room' | 'memo' | 'retry' | 'review';
	title: string;
	room?: Room;
	floor?: Floor;
	qids: string[];
	pos: number;
	picks: (number | null)[];
	finished: boolean;
	/** 解き直しのとき、元の部屋のクリア記録は更新しない */
	countsForRoom: boolean;
	/** 総会の振り返りから来たとき戻る先 */
	back?: string;
};

type ExamSession = {
	exam: Exam;
	exempt: boolean;
	qids: string[];
	pos: number;
	picks: (number | null)[];
	deadline: number;
	finished: boolean;
};

type View =
	| { name: 'home' }
	| { name: 'lesson' }
	| { name: 'soukai' }
	| { name: 'exam' }
	| { name: 'record' };

export class App {
	private store = S.load();
	private view: View = { name: 'home' };
	private lesson: Lesson | null = null;
	private exam: ExamSession | null = null;
	private timer: number | undefined;
	private talk = '';
	private mood: 'smile' | 'happy' | 'think' = 'smile';
	private stage: HTMLElement;
	private panel: HTMLElement;

	constructor(
		private root: HTMLElement,
		private data: AppData,
	) {
		this.stage = root.querySelector('[data-stage]')!;
		this.panel = root.querySelector('[data-panel]')!;
		root.addEventListener('click', (e) => this.onClick(e));
		document.addEventListener('keydown', (e) => this.onKey(e));
		window.addEventListener('hashchange', () => this.route());
		this.route();
	}

	/* ----- データの取り出し ----- */

	private q(id: string) {
		return this.data.questions[id];
	}

	private roomById(id: string) {
		for (const f of this.data.floors) {
			const r = f.rooms.find((x) => x.id === id);
			if (r) return { room: r, floor: f };
		}
		return null;
	}

	private cleared(room: Room) {
		return !!this.store.rooms[room.id];
	}

	private perfect(room: Room) {
		const r = this.store.rooms[room.id];
		return !!r && r.best >= r.total;
	}

	/** 次に行くとよい部屋（1F から順に、まだ明かりのついていない最初の部屋） */
	private nextRoom() {
		for (const f of this.data.floors) for (const r of f.rooms) if (!this.cleared(r)) return { room: r, floor: f };
		return null;
	}

	private keys() {
		return Object.keys(this.store.rooms).length;
	}

	private daysLeft() {
		const t = new Date(this.data.examDay + 'T00:00:00').getTime();
		return Math.max(0, Math.ceil((t - Date.now()) / 86_400_000));
	}

	/* ----- 画面の切り替え ----- */

	private route() {
		const h = location.hash.replace(/^#\/?/, '');
		const [head, arg] = h.split('/');
		if (this.exam && !this.exam.finished && head !== 'soukai') {
			if (!confirm('総会（模試）の途中です。やめてもよいですか？')) {
				history.replaceState(null, '', `#/soukai/${this.exam.exam.id}`);
				return;
			}
			this.stopExam();
		}
		window.clearInterval(this.timer);
		if (head === 'room' && arg) {
			const hit = this.roomById(arg);
			if (hit) return this.startLesson({ kind: 'room', title: `${hit.room.no}号室`, room: hit.room, floor: hit.floor, qids: hit.room.qids, countsForRoom: true });
		}
		if (head === 'memo') {
			const ids = S.dueIds(this.store).slice(0, 10);
			return this.startLesson({ kind: 'memo', title: 'メモ帳の復習', qids: ids, countsForRoom: false });
		}
		if (head === 'soukai') {
			const exam = this.data.exams.find((e) => e.id === arg);
			if (exam) {
				if (!this.exam || this.exam.exam.id !== exam.id) {
					this.view = { name: 'soukai' };
					this.render();
					return;
				}
				this.view = { name: 'exam' };
				this.startTimer();
				return this.render();
			}
			this.exam = null;
			this.view = { name: 'soukai' };
			return this.render();
		}
		if (head === 'record') {
			this.view = { name: 'record' };
			return this.render();
		}
		this.lesson = null;
		this.view = { name: 'home' };
		this.render();
	}

	private startLesson(l: Omit<Lesson, 'pos' | 'picks' | 'finished'>) {
		this.lesson = { ...l, pos: 0, picks: l.qids.map(() => null), finished: false };
		this.view = { name: 'lesson' };
		this.mood = 'smile';
		this.render();
		this.scrollTop();
	}

	private scrollTop() {
		this.panel.scrollIntoView({ block: 'start', behavior: 'smooth' });
	}

	/* ----- 操作 ----- */

	private onClick(e: Event) {
		const el = (e.target as HTMLElement).closest<HTMLElement>('[data-act]');
		if (!el) return;
		const act = el.dataset.act!;
		const arg = el.dataset.arg ?? '';
		switch (act) {
			case 'choose':
				return this.choose(Number(arg));
			case 'next':
				return this.next();
			case 'retry':
				return this.retryWrong();
			case 'review':
				return this.reviewExamQuestion(arg);
			case 'exam-start':
				return this.startExam(arg);
			case 'exam-go':
				return this.examGo(Number(arg));
			case 'exam-pick':
				return this.examPick(Number(arg));
			case 'exam-finish':
				return this.finishExam();
			case 'export':
				return this.exportRecord();
			case 'import':
				return (this.root.querySelector('[data-import-file]') as HTMLInputElement)?.click();
			case 'clear':
				if (confirm('学習記録をすべて消します。よろしいですか？')) {
					S.clear();
					this.store = S.load();
					this.render();
				}
				return;
		}
	}

	private onKey(e: KeyboardEvent) {
		const tag = (e.target as HTMLElement)?.tagName;
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.metaKey || e.ctrlKey || e.altKey) return;
		const n = Number(e.key);
		if (this.view.name === 'lesson' && this.lesson && !this.lesson.finished) {
			const q = this.q(this.lesson.qids[this.lesson.pos]);
			const answered = this.lesson.picks[this.lesson.pos] !== null;
			if (n >= 1 && n <= q.choices.length && !answered) this.choose(n);
			else if ((e.key === 'Enter' || e.key === 'ArrowRight') && answered) {
				e.preventDefault();
				this.next();
			}
		} else if (this.view.name === 'exam' && this.exam && !this.exam.finished) {
			const q = this.q(this.exam.qids[this.exam.pos]);
			if (n >= 1 && n <= q.choices.length) this.examPick(n);
			else if (e.key === 'ArrowRight') this.examGo(this.exam.pos + 1);
			else if (e.key === 'ArrowLeft') this.examGo(this.exam.pos - 1);
		}
	}

	private choose(n: number) {
		const l = this.lesson;
		if (!l || l.finished || l.picks[l.pos] !== null) return;
		l.picks[l.pos] = n;
		const q = this.q(l.qids[l.pos]);
		const ok = q.answer.includes(n);
		S.recordAnswer(this.store, q.id, ok);
		S.save(this.store);
		this.mood = ok ? 'happy' : 'think';
		this.render();
		this.panel.querySelector('[data-keeper]')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
	}

	private next() {
		const l = this.lesson;
		if (!l || l.picks[l.pos] === null) return;
		if (l.kind === 'review' && l.back) {
			location.hash = l.back;
			return;
		}
		if (l.pos < l.qids.length - 1) {
			l.pos += 1;
			this.mood = 'smile';
			this.render();
			this.scrollTop();
			return;
		}
		l.finished = true;
		const correct = l.qids.filter((id, i) => this.q(id).answer.includes(l.picks[i] ?? -1)).length;
		if (l.room && l.countsForRoom) {
			S.recordRoom(this.store, l.room.id, correct, l.qids.length);
			S.save(this.store);
		}
		this.mood = 'happy';
		this.render();
		this.scrollTop();
	}

	private retryWrong() {
		const l = this.lesson;
		if (!l) return;
		const wrong = l.qids.filter((id, i) => !this.q(id).answer.includes(l.picks[i] ?? -1));
		if (!wrong.length) return;
		this.startLesson({ kind: 'retry', title: l.room ? `${l.room.no}号室（解き直し）` : 'もう一度', room: l.room, floor: l.floor, qids: wrong, countsForRoom: false });
	}

	/* ----- 総会（模試） ----- */

	private startExam(arg: string) {
		const [id, mode] = arg.split(':');
		const exam = this.data.exams.find((e) => e.id === id);
		if (!exam) return;
		const exempt = mode === 'exempt';
		const qids = exempt ? exam.qids.filter((qid) => this.q(qid).no <= 45) : exam.qids;
		this.exam = { exam, exempt, qids, pos: 0, picks: qids.map(() => null), deadline: Date.now() + (exempt ? 110 : 120) * 60_000, finished: false };
		location.hash = `#/soukai/${exam.id}`;
	}

	private startTimer() {
		window.clearInterval(this.timer);
		this.timer = window.setInterval(() => {
			const x = this.exam;
			if (!x || x.finished) return window.clearInterval(this.timer);
			const left = Math.max(0, x.deadline - Date.now());
			const el = this.root.querySelector('[data-timer]');
			if (el) {
				el.textContent = `残り ${Math.floor(left / 60000)}:${String(Math.floor((left % 60000) / 1000)).padStart(2, '0')}`;
				el.classList.toggle('is-warn', left < 600_000);
			}
			if (left === 0) {
				alert('試験時間が終わりました。採点します。');
				this.finishExam(true);
			}
		}, 1000);
	}

	private stopExam() {
		window.clearInterval(this.timer);
		this.exam = null;
	}

	private examGo(i: number) {
		const x = this.exam;
		if (!x || i < 0 || i >= x.qids.length) return;
		x.pos = i;
		this.render();
		this.scrollTop();
	}

	private examPick(n: number) {
		const x = this.exam;
		if (!x || x.finished) return;
		x.picks[x.pos] = n;
		this.render();
	}

	private finishExam(force = false) {
		const x = this.exam;
		if (!x || x.finished) return;
		const blank = x.picks.filter((p) => p === null).length;
		if (!force && blank && !confirm(`未解答が ${blank} 問あります。採点しますか？`)) return;
		x.finished = true;
		window.clearInterval(this.timer);
		let score = 0;
		x.qids.forEach((id, i) => {
			const p = x.picks[i];
			if (p === null) return;
			const ok = this.q(id).answer.includes(p);
			if (ok) score += 1;
			S.recordAnswer(this.store, id, ok);
		});
		this.store.exams.push({
			exam: x.exam.id,
			label: x.exam.label + (x.exempt ? '（5問免除）' : ''),
			score,
			total: x.qids.length,
			passMark: x.exempt ? x.exam.passMarkExempt : x.exam.passMark,
			t: Date.now(),
		});
		S.save(this.store);
		this.mood = 'happy';
		this.render();
		this.scrollTop();
	}

	private reviewExamQuestion(id: string) {
		const x = this.exam;
		if (!x) return;
		const i = x.qids.indexOf(id);
		this.lesson = {
			kind: 'review',
			title: `${x.exam.label} 問${this.q(id).no}`,
			qids: [id],
			pos: 0,
			picks: [x.picks[i] ?? 0],
			finished: false,
			countsForRoom: false,
			back: `#/soukai/${x.exam.id}`,
		};
		this.mood = x.picks[i] !== null && this.q(id).answer.includes(x.picks[i]!) ? 'happy' : 'think';
		this.view = { name: 'lesson' };
		history.pushState(null, '', `#/soukai/${x.exam.id}/review`);
		this.render();
		this.scrollTop();
	}

	/* ----- 記録の書き出し・読み込み ----- */

	private exportRecord() {
		const blob = new Blob([S.exportJson(this.store)], { type: 'application/json' });
		const a = document.createElement('a');
		a.href = URL.createObjectURL(blob);
		a.download = `mansion-kouryaku-${S.dayKey()}.json`;
		a.click();
		URL.revokeObjectURL(a.href);
	}

	bindImport() {
		const input = this.root.querySelector<HTMLInputElement>('[data-import-file]');
		input?.addEventListener('change', async () => {
			const f = input.files?.[0];
			if (!f) return;
			try {
				this.store = S.importJson(await f.text());
				S.save(this.store);
				this.render();
			} catch {
				alert('読み込めませんでした。書き出したファイルを選んでください。');
			}
		});
	}

	/* ---------- 描画 ---------- */

	private render() {
		this.panel.innerHTML = this.renderPanel();
		this.stage.innerHTML = this.renderStage();
		if (this.view.name === 'record') this.bindImport();
		if (this.view.name === 'exam' && this.exam && !this.exam.finished) this.startTimer();
	}

	/* 左：マンション */
	private renderStage() {
		const active = this.lesson?.room?.id ?? (this.view.name === 'home' ? this.nextRoom()?.room.id : undefined);
		const floors = [...this.data.floors]
			.reverse()
			.map((f) => {
				const wins = f.rooms
					.map((r) => {
						const cls = ['win'];
						if (this.cleared(r)) cls.push(this.perfect(r) ? 'win-star' : 'win-lit');
						if (r.id === active) cls.push('win-cur');
						const state = this.cleared(r) ? (this.perfect(r) ? '全問正解' : 'クリア') : '未クリア';
						return `<a class="${cls.join(' ')}" href="#/room/${r.id}" aria-label="${r.no}号室（${esc(f.short)}・${state}）" title="${r.no}号室">${r.no % 100}</a>`;
					})
					.join('');
				const done = f.rooms.filter((r) => this.cleared(r)).length;
				return `<div class="floor${done ? ' floor-on' : ''}">
					<span class="floor-label"><b>${f.floor}F</b> ${esc(f.short)}<small>${done}/${f.rooms.length}</small></span>
					<span class="floor-wins">${wins}</span>
				</div>`;
			})
			.join('');
		const allDone = this.data.floors.every((f) => f.rooms.every((r) => this.cleared(r)));
		return `
			<div class="sky" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i><i></i><span class="moon"></span></div>
			<div class="stage-title">
				<a href="#/" class="logo">マンション攻略</a>
				<span>管理業務主任者試験 ・ 1階から屋上（合格）まで</span>
			</div>
			<div class="bldg">
				<div class="roof"><svg width="30" height="40" viewBox="0 0 34 46" aria-hidden="true"><path d="M4 2v44" stroke="#C5CDE0" stroke-width="3"></path><path d="M6 4h24l-6 8 6 8H6z" fill="${allDone ? '#FFC857' : '#FF7A59'}"></path></svg><span>屋上 ＝ 合格</span></div>
				<div class="bldg-top"></div>
				<div class="bldg-body">${floors}</div>
				<div class="bldg-base"><span class="door"></span></div>
			</div>
			<div class="ground"></div>
			<div class="keeper-talk">
				${keeperSvg(64, this.mood)}
				<p class="talk-bubble">${esc(this.stageTalk())}</p>
			</div>`;
	}

	private stageTalk() {
		const v = this.view.name;
		if (v === 'home') {
			const due = S.dueIds(this.store).length;
			if (due) return `メモ帳に復習が ${due} 件たまってるよ。先に片づけると気持ちいいよ。`;
			const nx = this.nextRoom();
			if (!nx) return '全部の部屋に明かりがついた！あとは総会（模試）で仕上げよう。';
			return this.keys() ? `おかえり！次は ${nx.room.no}号室の相談だよ。` : `ようこそ！まずは ${nx.room.no}号室の相談から始めよう。`;
		}
		if (v === 'lesson' && this.lesson) {
			const l = this.lesson;
			if (l.finished) return l.kind === 'room' ? '明かりがついたね！カギを1本どうぞ。' : 'おつかれさま！';
			const p = l.picks[l.pos];
			if (p === null) return l.pos === 0 ? '相談は全部で ' + l.qids.length + ' 件。落ち着いて読もう。' : 'つぎの相談だよ。';
			const ok = this.q(l.qids[l.pos]).answer.includes(p);
			return ok ? pick(PRAISE, hash(l.qids[l.pos])) : '間違えたところは、右の解説で一緒に確認しよう。';
		}
		if (v === 'exam') return this.exam?.finished ? '採点が終わったよ。間違えた問題は解説で確認しよう。' : '総会の時間だ。わからない問題は飛ばして、あとで戻ろう。';
		if (v === 'soukai') return '総会（模試）は本番と同じ50問・2時間。腕試しにどうぞ。';
		return 'ここまでの記録だよ。苦手な階が見えてくるね。';
	}

	/* 右：中身 */
	private renderPanel() {
		const s = this.store;
		const chips = `<div class="chips">
			<span class="chip">${keySvg()}カギ <b>${this.keys()}</b>本</span>
			<span class="chip">${flameSvg()}<b>${S.streak(s)}</b>日連続</span>
			<span class="chip">今日 <b>${S.todayCount(s)}</b> / ${S.DAILY_GOAL}問</span>
		</div>`;
		const nav = `<nav class="tabs" aria-label="メニュー">
			<a href="#/" class="${this.view.name === 'home' ? 'on' : ''}">攻略マップ</a>
			<a href="#/memo" class="${this.lesson?.kind === 'memo' ? 'on' : ''}">メモ帳</a>
			<a href="#/soukai" class="${this.view.name === 'soukai' || this.view.name === 'exam' ? 'on' : ''}">総会（模試）</a>
			<a href="#/record" class="${this.view.name === 'record' ? 'on' : ''}">記録</a>
			<a href="${this.data.base}guide/">ガイド・ノート</a>
		</nav>`;
		let body = '';
		switch (this.view.name) {
			case 'home':
				body = this.renderHome();
				break;
			case 'lesson':
				body = this.lesson?.finished ? this.renderResult() : this.renderLesson();
				break;
			case 'soukai':
				body = this.renderSoukai();
				break;
			case 'exam':
				body = this.exam?.finished ? this.renderExamResult() : this.renderExam();
				break;
			case 'record':
				body = this.renderRecord();
				break;
		}
		return `<div class="panel-head">${nav}${chips}</div>${body}`;
	}

	private renderHome() {
		const nx = this.nextRoom();
		const due = S.dueIds(this.store).length;
		const waiting = S.waitingCount(this.store);
		const next = nx
			? `<section class="card card-hero">
				<div class="hero-meta"><span class="room-plate">${nx.room.no}号室</span><span>${nx.floor.floor}F ${esc(nx.floor.label)} ・ 相談 ${nx.room.qids.length}件</span></div>
				<h1 class="hero-title">「${esc(nx.floor.short)}のこと、ちょっと教えて！」</h1>
				<p class="muted">住人さんの相談に、試験の知識で答えよう。全部答えると部屋の明かりがついてカギがもらえます。間違えても、管理人さんが「なぜ違うか」を教えてくれます。</p>
				<p><a class="btn btn-go" href="#/room/${nx.room.id}">相談を聞きに行く</a></p>
			</section>`
			: `<section class="card card-hero"><h1 class="hero-title">全部の部屋に明かりがつきました！</h1><p class="muted">総会（模試）で本番の練習をしよう。</p><p><a class="btn btn-go" href="#/soukai">総会へ</a></p></section>`;
		const floors = this.data.floors
			.map((f) => {
				const done = f.rooms.filter((r) => this.cleared(r)).length;
				const first = f.rooms.find((r) => !this.cleared(r)) ?? f.rooms[0];
				return `<a class="floor-row" href="#/room/${first.id}">
					<span class="floor-no">${f.floor}F</span>
					<span class="floor-name">${esc(f.label)}</span>
					<span class="bar"><span style="width:${Math.round((done / f.rooms.length) * 100)}%"></span></span>
					<span class="floor-count">${done} / ${f.rooms.length}部屋</span>
				</a>`;
			})
			.join('');
		return `${next}
			<div class="grid3">
				<section class="card">
					<span class="label">メモ帳（復習）</span>
					<span class="big">${due}件</span>
					<span class="muted small">${due ? '間違えた相談がもう一度来ています' : waiting ? `あと ${waiting}件が、日をおいて戻ってきます` : '間違えた相談は、ここに書きとめられます'}</span>
					${due ? `<a class="btn btn-sub" href="#/memo">復習する</a>` : ''}
				</section>
				<section class="card">
					<span class="label">総会（模試）</span>
					<span class="big">${this.data.exams.length}回分</span>
					<span class="muted small">過去問50問・2時間の本番形式</span>
					<a class="btn btn-sub" href="#/soukai">総会を開く</a>
				</section>
				<section class="card">
					<span class="label">本番まで</span>
					<span class="big">${this.daysLeft()}日</span>
					<span class="muted small">2026年12月6日（日）13:00〜15:00</span>
					<a class="btn btn-sub" href="${this.data.base}guide/exam/">試験の概要</a>
				</section>
			</div>
			<section class="card">
				<h2 class="h2">各階の攻略状況</h2>
				<div class="floors">${floors}</div>
			</section>`;
	}

	/** 住人さんの相談（問題）カード */
	private questionCard(q: QItem, who: string) {
		const statements = q.statements?.length
			? `<dl class="stmts">${q.statements.map((s) => `<div><dt>${esc(s.label)}</dt><dd>${esc(s.text)}</dd></div>`).join('')}</dl>`
			: '';
		const figure = q.images?.length
			? `<div class="figure">${q.images.map((src) => `<img src="${esc(src)}" alt="問題の図表" loading="lazy">`).join('')}</div>`
			: '';
		return `<div class="ask">
			${residentSvg(q.id)}
			<div class="ask-bubble">
				<span class="ask-who">${esc(who)} ・ ${esc(catShort(q.cat))} ・ ${esc(q.set)} 問${q.no}</span>
				${figure ? `${figure}<span class="sr">${esc(q.stem)}</span>` : `<p class="ask-text">${esc(q.stem)}</p>${statements}`}
			</div>
		</div>`;
	}

	private choiceButtons(q: QItem, picked: number | null, reveal: boolean, act: string) {
		const textHidden = !!q.images?.length;
		return `<div class="answers${textHidden ? ' answers-row' : ''}">${q.choices
			.map((c, i) => {
				const n = i + 1;
				const cls = ['ans'];
				if (reveal) {
					if (q.answer.includes(n)) cls.push('ans-ok');
					else if (picked === n) cls.push('ans-ng');
					else cls.push('ans-dim');
				} else if (picked === n) cls.push('ans-picked');
				const tag = reveal
					? q.answer.includes(n)
						? '<span class="tag tag-ok">正解</span>'
						: picked === n
							? '<span class="tag tag-ng">あなたの回答</span>'
							: ''
					: '';
				return `<button type="button" class="${cls.join(' ')}" data-act="${act}" data-arg="${n}" ${reveal ? 'aria-disabled="true"' : ''}>
					<span class="ans-no">${choiceMark(q, i)}</span>${textHidden ? '' : `<span class="ans-text">${esc(c)}</span>`}${tag}
				</button>`;
			})
			.join('')}</div>`;
	}

	/** 管理人さんの解説 */
	private keeperCard(q: QItem, picked: number) {
		const ok = q.answer.includes(picked);
		const notes = q.choiceNotes ?? [];
		const ansNo = q.answer[0];
		const parts: string[] = [];
		if (!ok && picked > 0) {
			parts.push(`<div class="why why-ng">
				<p class="why-title">「${esc(choiceMark(q, picked - 1))}」を選んだね</p>
				${this.polarityHint(q)}
				<p>${notes[picked - 1] ? rich(notes[picked - 1]) : 'この選択肢の解説はまだ準備中なんだ。'}</p>
			</div>`);
		}
		parts.push(`<div class="why why-ok">
			<p class="why-title">正解は ${q.answer.map((n) => esc(choiceMark(q, n - 1))).join('・')}</p>
			${notes[ansNo - 1] ? `<p>${rich(notes[ansNo - 1])}</p>` : ''}
			${q.answer.length > 1 ? '<p class="small">この問題は、試験実施機関の発表で複数の選択肢が正解とされています。</p>' : ''}
		</div>`);
		if (q.statementNotes?.length) {
			parts.push(`<ul class="stmt-notes">${q.statementNotes
				.map((s) => `<li><span class="mark ${s.correct ? 'mark-ok' : 'mark-ng'}">${esc(s.label)} ${s.correct ? '○' : '×'}</span><span>${rich(s.note)}</span></li>`)
				.join('')}</ul>`);
		}
		if (q.explanation) parts.push(`<div class="point"><p class="label">ポイント</p><p>${rich(q.explanation)}</p></div>`);
		if (q.law) parts.push(`<p class="law">根拠：${esc(q.law)}</p>`);
		if (q.amendment) parts.push(`<div class="amend"><p class="label">法改正の注意</p><p>${rich(q.amendment)}</p></div>`);
		else if (q.oldLaw) parts.push(`<div class="amend"><p class="label">法改正の注意</p><p>この問題は令和8年4月施行の区分所有法等の改正より前の出題です。現在の法令では結論が変わる場合があります。</p></div>`);
		if (!q.explanation && !notes.length) {
			parts.push(`<p class="muted small">この問題の解説はまだ準備中なんだ。${q.pdf ? `<a href="${esc(q.pdf)}" target="_blank" rel="noopener">問題冊子（公式PDF）</a>も見てみてね。` : ''}</p>`);
		}
		const others = notes.length
			? `<details class="others"><summary>ほかの選択肢の解説も見る</summary><ol>${notes
					.map((n, i) => `<li><b>${esc(choiceMark(q, i))}</b> ${rich(n)}</li>`)
					.join('')}</ol></details>`
			: '';
		if (q.needsCheck) parts.push('<p class="muted small">※ この解説には、まだ確認中の点があります。</p>');
		return `<section class="keeper ${ok ? 'is-ok' : 'is-ng'}" data-keeper>
			<div class="keeper-head">${keeperSvg(52, ok ? 'happy' : 'think')}<p class="keeper-title">${esc(ok ? pick(PRAISE, hash(q.id)) : pick(OOPS, hash(q.id)))}</p></div>
			${parts.join('')}
			${others}
			${q.source ? `<p class="source">${esc(q.source)}</p>` : ''}
		</section>`;
	}

	/** 「不適切なものを選ぶ問題」で正しい記述を選んだ、などの取り違えを説明する */
	private polarityHint(q: QItem) {
		if (q.statements?.length || q.choices.length !== 4 || q.images?.length) return '';
		if (/不適切な|誤っている|誤りである|誤っているもの/.test(q.stem))
			return '<p class="hint">この問題は「不適切なもの（誤っているもの）」を選ぶ問題。選んだ記述の内容が正しいなら、答えにはならないよ。</p>';
		if (/適切な|正しい/.test(q.stem))
			return '<p class="hint">この問題は「適切なもの（正しいもの）」を選ぶ問題。選んだ記述のどこに誤りがあるか見てみよう。</p>';
		return '';
	}

	private renderLesson() {
		const l = this.lesson!;
		if (!l.qids.length) {
			return `<section class="card"><h1 class="h1">メモ帳は空っぽです</h1><p class="muted">間違えた相談は、ここに書きとめられて、日をおいてもう一度出てきます。</p><p><a class="btn btn-go" href="#/">攻略マップに戻る</a></p></section>`;
		}
		const q = this.q(l.qids[l.pos]);
		const picked = l.picks[l.pos];
		const answered = picked !== null;
		const segs = l.qids
			.map((id, i) => {
				const p = l.picks[i];
				const st = p === null ? (i === l.pos ? 'cur' : '') : this.q(id).answer.includes(p) ? 'ok' : 'ng';
				return `<span class="seg ${st}"></span>`;
			})
			.join('');
		const who = l.room ? `${l.room.no}号室の住人` : l.kind === 'memo' ? 'メモ帳から' : '振り返り';
		const isLast = l.pos === l.qids.length - 1;
		const nextLabel = l.kind === 'review' ? '結果に戻る' : isLast ? (l.room && l.countsForRoom ? '部屋を解決する' : '結果を見る') : '次の相談へ';
		return `<div class="lesson-bar">
				<a href="${l.back ?? '#/'}" class="back">← ${l.kind === 'review' ? '結果に戻る' : '部屋を出る'}</a>
				<span class="lesson-title">${esc(l.title)} ・ ${l.pos + 1} / ${l.qids.length}</span>
			</div>
			<div class="segs" style="grid-template-columns:repeat(${l.qids.length},minmax(0,1fr))">${segs}</div>
			${this.questionCard(q, who)}
			<p class="label">あなたの回答${answered ? '' : '<span class="muted small">（キーボードの数字キーでも選べます）</span>'}</p>
			${this.choiceButtons(q, picked, answered, 'choose')}
			${answered ? this.keeperCard(q, picked!) : ''}
			${answered ? `<p class="next-row"><button type="button" class="btn btn-go" data-act="next">${nextLabel}</button></p>` : ''}`;
	}

	private renderResult() {
		const l = this.lesson!;
		const results = l.qids.map((id, i) => ({ q: this.q(id), ok: this.q(id).answer.includes(l.picks[i] ?? -1) }));
		const correct = results.filter((r) => r.ok).length;
		const wrong = results.length - correct;
		const nx = this.nextRoom();
		const list = results
			.map((r) => `<li>${r.ok ? okSvg : ngSvg}<span><small>${esc(r.q.set)} 問${r.q.no} ・ ${esc(catShort(r.q.cat))}</small>${esc(r.q.stem.slice(0, 60))}${r.q.stem.length > 60 ? '…' : ''}</span></li>`)
			.join('');
		const solved = l.kind === 'room' || (l.kind === 'retry' && l.room);
		return `<section class="card card-hero">
				<div class="result-head">
					<span class="key-badge">${keySvg(44)}</span>
					<div>
						<h1 class="hero-title">${solved && l.room ? `${l.room.no}号室 解決！` : l.kind === 'memo' ? '復習おわり！' : 'おつかれさま！'}</h1>
						<p class="result-score">${correct} / ${results.length} 件 正解${l.kind === 'room' ? ' ・ カギを1本手に入れた' : ''}</p>
					</div>
				</div>
				${wrong ? `<p class="note-box">間違えた ${wrong} 件はメモ帳に書きとめました。すぐに解き直すこともできます。</p>` : '<p class="note-box note-ok">全問正解！この部屋には星がつきました。</p>'}
				<div class="btn-row">
					${wrong ? '<button type="button" class="btn btn-sub" data-act="retry">間違えた相談にもう一度答える</button>' : ''}
					${nx ? `<a class="btn btn-go" href="#/room/${nx.room.id}">次の部屋（${nx.room.no}号室）へ</a>` : ''}
					<a class="btn btn-sub" href="#/">攻略マップに戻る</a>
				</div>
			</section>
			<section class="card"><h2 class="h2">今回の相談</h2><ul class="result-list">${list}</ul></section>`;
	}

	private renderSoukai() {
		const last = (id: string) => [...this.store.exams].reverse().find((e) => e.exam === id);
		const rows = this.data.exams
			.map((e) => {
				const l = last(e.id);
				return `<div class="exam-row">
					<div><b>${esc(e.label)}</b><span class="muted small">合格基準点 ${e.passMark ?? '—'}問 ・ <a href="${esc(e.pdf)}" target="_blank" rel="noopener">問題冊子（公式PDF）</a></span>${l ? `<span class="small">前回 ${l.score}/${l.total}</span>` : ''}</div>
					<div class="btn-row">
						<button type="button" class="btn btn-go" data-act="exam-start" data-arg="${e.id}:full">50問・2時間</button>
						<button type="button" class="btn btn-sub" data-act="exam-start" data-arg="${e.id}:exempt">5問免除（45問）</button>
					</div>
				</div>`;
			})
			.join('');
		return `<section class="card">
				<h1 class="h1">総会（模試）</h1>
				<p class="muted">本番と同じ形式で、1年分の過去問を解きます。途中で正解は出ません。最後に採点して、合格基準点と比べます。間違えた問題はメモ帳に入ります。</p>
				<div class="exam-list">${rows}</div>
				<p class="muted small">令和2年度は問題冊子が画像のため、まだ収録していません。過去問の出典：一般社団法人マンション管理業協会「管理業務主任者試験問題」各年度。</p>
			</section>`;
	}

	private renderExam() {
		const x = this.exam!;
		const q = this.q(x.qids[x.pos]);
		const grid = x.qids
			.map((_, i) => `<button type="button" class="cell${x.picks[i] !== null ? ' done' : ''}${i === x.pos ? ' cur' : ''}" data-act="exam-go" data-arg="${i}" aria-label="問${i + 1}">${i + 1}</button>`)
			.join('');
		return `<div class="lesson-bar">
				<span class="lesson-title">総会 ・ ${esc(x.exam.label)}${x.exempt ? '（5問免除）' : ''} ・ 問 ${x.pos + 1} / ${x.qids.length}</span>
				<span class="timer" data-timer></span>
			</div>
			${this.questionCard(q, '総会の議題')}
			${this.choiceButtons(q, x.picks[x.pos], false, 'exam-pick')}
			<div class="btn-row spread">
				<button type="button" class="btn btn-sub" data-act="exam-go" data-arg="${x.pos - 1}" ${x.pos === 0 ? 'disabled' : ''}>← 前へ</button>
				<button type="button" class="btn btn-go" data-act="exam-finish">採点する</button>
				<button type="button" class="btn btn-sub" data-act="exam-go" data-arg="${x.pos + 1}" ${x.pos === x.qids.length - 1 ? 'disabled' : ''}>次へ →</button>
			</div>
			<section class="card"><p class="label">問題一覧（解答済み ${x.picks.filter((p) => p !== null).length} / ${x.qids.length}）</p><div class="cells">${grid}</div></section>`;
	}

	private renderExamResult() {
		const x = this.exam!;
		const res = x.qids.map((id, i) => ({ q: this.q(id), p: x.picks[i], ok: x.picks[i] !== null && this.q(id).answer.includes(x.picks[i]!) }));
		const score = res.filter((r) => r.ok).length;
		const pm = x.exempt ? x.exam.passMarkExempt : x.exam.passMark;
		const byCat = CATEGORIES.map((c) => {
			const rs = res.filter((r) => r.q.cat === c.id);
			return rs.length ? `<tr><td>${esc(c.label)}</td><td>${rs.filter((r) => r.ok).length} / ${rs.length}</td><td><span class="bar"><span style="width:${Math.round((rs.filter((r) => r.ok).length / rs.length) * 100)}%"></span></span></td></tr>` : '';
		}).join('');
		const cells = res
			.map((r) => `<button type="button" class="cell ${r.ok ? 'ok' : 'ng'}" data-act="review" data-arg="${r.q.id}" aria-label="問${r.q.no}の解説">${r.q.no}</button>`)
			.join('');
		return `<section class="card card-hero">
				<p class="label">総会 ・ ${esc(x.exam.label)}${x.exempt ? '（5問免除）' : ''}</p>
				<h1 class="hero-title">${score} / ${x.qids.length} 問 正解</h1>
				${pm ? `<p class="judge ${score >= pm ? 'is-ok' : 'is-ng'}">${score >= pm ? `合格基準点（${pm}問）を超えました！` : `合格基準点（${pm}問）まで あと ${pm - score}問`}</p>` : ''}
				<div class="btn-row"><a class="btn btn-sub" href="#/soukai">ほかの年度</a><a class="btn btn-go" href="#/memo">間違えた問題をメモ帳で復習</a></div>
			</section>
			<section class="card"><h2 class="h2">分野別</h2><table class="table">${byCat}</table></section>
			<section class="card"><h2 class="h2">問題ごとの結果（押すと解説）</h2><div class="cells">${cells}</div></section>`;
	}

	private renderRecord() {
		const s = this.store;
		const rows = this.data.floors
			.map((f) => {
				const ids = f.rooms.flatMap((r) => r.qids);
				const done = ids.filter((id) => s.q[id]);
				const ok = done.filter((id) => s.q[id].last).length;
				const rate = done.length ? ok / done.length : 0;
				return `<tr><td>${f.floor}F ${esc(f.label)}</td><td>${done.length} / ${ids.length}</td><td>${done.length ? Math.round(rate * 100) + '%' : '—'}</td><td><span class="bar"><span style="width:${Math.round(rate * 100)}%"></span></span></td></tr>`;
			})
			.join('');
		const exams = s.exams.length
			? `<table class="table"><tr><th>日付</th><th>年度</th><th>得点</th><th>合格基準点</th></tr>${[...s.exams]
					.reverse()
					.map((e) => `<tr><td>${S.dayKey(e.t)}</td><td>${esc(e.label)}</td><td>${e.score} / ${e.total}</td><td>${e.passMark ?? '—'}</td></tr>`)
					.join('')}</table>`
			: '<p class="muted">まだ総会（模試）の記録はありません。</p>';
		return `<section class="card">
				<h1 class="h1">記録</h1>
				<p class="muted">解いた問題 <b>${Object.keys(s.q).length}</b> / ${Object.keys(this.data.questions).length} 問 ・ カギ ${this.keys()}本 ・ ${S.streak(s)}日連続</p>
				<h2 class="h2">階ごとの正答率（直近の解答）</h2>
				<table class="table"><tr><th>階</th><th>解いた問題</th><th>正答率</th><th></th></tr>${rows}</table>
			</section>
			<section class="card"><h2 class="h2">総会（模試）の記録</h2>${exams}</section>
			<section class="card">
				<h2 class="h2">記録の保存</h2>
				<p class="muted small">記録はこのブラウザの中だけに保存されています。別の端末に移すときは書き出して、移した先で読み込んでください。</p>
				<div class="btn-row">
					<button type="button" class="btn btn-sub" data-act="export">記録を書き出す</button>
					<button type="button" class="btn btn-sub" data-act="import">記録を読み込む</button>
					<input type="file" accept="application/json" data-import-file hidden>
					<button type="button" class="btn btn-danger" data-act="clear">記録をすべて消す</button>
				</div>
			</section>`;
	}
}
