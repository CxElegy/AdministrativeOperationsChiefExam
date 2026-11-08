import { addResult, loadRecord } from './record';
import type { QuizItem, QuizOptions } from './types';

const esc = (s: string) =>
	s.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]!);

/** 解説用のごく簡単な記法: 改行 / **太字** / `コード` */
const rich = (s: string) =>
	esc(s)
		.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
		.replace(/`(.+?)`/g, '<code>$1</code>')
		.replace(/\n/g, '<br>');

type Status = 'unanswered' | 'correct' | 'wrong';

/**
 * 問題演習の画面。1 問ずつ表示し、練習モードでは解答直後に正誤と解説を出す。
 * 本番モードでは最後にまとめて採点する。
 */
export class QuizApp {
	private idx = 0;
	private picks: (number | null)[];
	private revealed: boolean[];
	private finished = false;
	private deadline = 0;
	private timer: number | undefined;

	constructor(
		private root: HTMLElement,
		private items: QuizItem[],
		private opts: QuizOptions,
	) {
		this.picks = items.map(() => null);
		this.revealed = items.map(() => false);
		if (opts.mode === 'exam' && opts.timeLimit) {
			this.deadline = Date.now() + opts.timeLimit * 60_000;
			this.timer = window.setInterval(() => this.tick(), 1000);
		}
		// 同じ場所で作り直したとき（間違えた問題の解き直しなど）に前のものを片付ける
		const host = root as HTMLElement & { __qzDispose?: () => void };
		host.__qzDispose?.();
		const onKey = (e: KeyboardEvent) => this.onKey(e);
		document.addEventListener('keydown', onKey);
		host.__qzDispose = () => {
			document.removeEventListener('keydown', onKey);
			window.clearInterval(this.timer);
		};
		this.render();
	}

	private status(i: number): Status {
		const p = this.picks[i];
		if (p === null) return 'unanswered';
		return this.items[i].answer.includes(p) ? 'correct' : 'wrong';
	}

	private showFeedback(i: number) {
		return this.opts.mode === 'practice' ? this.revealed[i] : this.finished;
	}

	private onKey(e: KeyboardEvent) {
		const tag = (e.target as HTMLElement)?.tagName;
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || e.metaKey || e.ctrlKey || e.altKey) return;
		if (!this.root.isConnected) return;
		const n = Number(e.key);
		const item = this.items[this.idx];
		if (n >= 1 && n <= item.choices.length) {
			this.choose(n);
		} else if (e.key === 'ArrowRight') {
			this.go(this.idx + 1);
		} else if (e.key === 'ArrowLeft') {
			this.go(this.idx - 1);
		}
	}

	private choose(n: number) {
		const i = this.idx;
		if (this.finished || (this.opts.mode === 'practice' && this.revealed[i])) return;
		this.picks[i] = n;
		if (this.opts.mode === 'practice') {
			this.revealed[i] = true;
			addResult(this.items[i].id, this.items[i].answer.includes(n));
		}
		this.render();
	}

	private go(i: number) {
		if (i < 0 || i >= this.items.length) return;
		this.idx = i;
		this.render();
		this.root.querySelector<HTMLElement>('.qz-card')?.focus({ preventScroll: true });
		const top = this.root.getBoundingClientRect().top + window.scrollY - 80;
		if (window.scrollY > top) window.scrollTo({ top });
	}

	private finish() {
		if (this.finished) return;
		const unanswered = this.picks.filter((p) => p === null).length;
		if (this.opts.mode === 'exam' && unanswered > 0 && Date.now() < this.deadline) {
			if (!confirm(`未解答が ${unanswered} 問あります。採点しますか？`)) return;
		}
		this.finished = true;
		window.clearInterval(this.timer);
		if (this.opts.mode === 'exam') {
			this.items.forEach((it, i) => {
				if (this.picks[i] !== null) addResult(it.id, it.answer.includes(this.picks[i]!));
			});
		}
		this.render();
		this.root.querySelector('.qz-summary')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	private tick() {
		const el = this.root.querySelector('.qz-timer');
		const left = Math.max(0, this.deadline - Date.now());
		if (el) {
			const m = Math.floor(left / 60000);
			const s = Math.floor((left % 60000) / 1000);
			el.textContent = `残り ${m}:${String(s).padStart(2, '0')}`;
			el.classList.toggle('qz-timer-warn', left < 10 * 60000);
		}
		if (left === 0) {
			alert('試験時間が終了しました。採点します。');
			this.finish();
		}
	}

	private render() {
		const item = this.items[this.idx];
		if (!item) {
			this.root.innerHTML = '<p class="qz-empty">条件に合う問題がありません。</p>';
			return;
		}
		const fb = this.showFeedback(this.idx);
		const pick = this.picks[this.idx];
		const rec = loadRecord()[item.id];
		const total = this.items.length;
		const answeredCount = this.picks.filter((p) => p !== null).length;

		const statements = item.statements?.length
			? `<dl class="qz-statements">${item.statements
					.map((s) => `<div><dt>${esc(s.label)}</dt><dd>${esc(s.text)}</dd></div>`)
					.join('')}</dl>`
			: '';

		const figure = !!item.images?.length;
		const choices = item.choices
			.map((c, k) => {
				const n = k + 1;
				const cls = ['qz-choice'];
				if (pick === n) cls.push('qz-picked');
				if (fb && item.answer.includes(n)) cls.push('qz-right');
				if (fb && pick === n && !item.answer.includes(n)) cls.push('qz-miss');
				const disabled = this.finished || (this.opts.mode === 'practice' && this.revealed[this.idx]);
				return `<li><button type="button" class="${cls.join(' ')}" data-n="${n}" ${disabled ? 'aria-disabled="true"' : ''}>
					<span class="qz-num">${n}</span><span class="qz-text">${figure ? '' : esc(c)}</span></button></li>`;
			})
			.join('');

		let feedback = '';
		if (fb) {
			const ok = pick !== null && item.answer.includes(pick);
			const verdict = pick === null ? '未解答' : ok ? '正解' : '不正解';
			feedback = `<div class="qz-feedback ${ok ? 'is-ok' : 'is-ng'}" role="status">
				<p class="qz-verdict">${verdict}<span>正解：${item.answer.join('・')}</span></p>
				${item.answer.length > 1 ? '<p class="qz-small">この問題は複数の選択肢が正解として扱われています（試験実施機関の発表による）。</p>' : ''}
				${
					item.explanation
						? `<div class="qz-expl">${rich(item.explanation)}</div>`
						: '<p class="qz-small">解説はまだありません。<code>src/data</code> の JSON に <code>explanation</code> を書くと表示されます。</p>'
				}
			</div>`;
		}

		const grid = this.items
			.map((_, i) => {
				const st = this.picks[i] === null ? 'unanswered' : this.showFeedback(i) ? this.status(i) : 'answered';
				return `<button type="button" class="qz-cell qz-${st} ${i === this.idx ? 'qz-current' : ''}" data-go="${i}" aria-label="${i + 1}問目">${i + 1}</button>`;
			})
			.join('');

		const correctCount = this.items.filter((_, i) => this.status(i) === 'correct').length;
		const summary = this.finished || (this.opts.mode === 'practice' && answeredCount === total) ? this.summary(correctCount) : '';

		this.root.innerHTML = `
			<div class="qz-bar">
				<span>${this.idx + 1} / ${total}</span>
				${this.opts.mode === 'exam' && !this.finished && this.opts.timeLimit ? '<span class="qz-timer"></span>' : ''}
				${this.opts.mode === 'practice' ? `<span>正解 ${correctCount} / 解答 ${answeredCount}</span>` : `<span>解答済み ${answeredCount}</span>`}
			</div>
			<article class="qz-card" tabindex="-1">
				<header class="qz-head">
					<span class="qz-badge">${esc(item.categoryLabel)}</span>
					<span class="qz-meta">${esc(item.set)} 問${item.no}</span>
					${rec ? `<span class="qz-meta">過去の記録 ${rec.c}/${rec.a} 正解${rec.last ? '' : '（前回×）'}</span>` : ''}
				</header>
				${
					figure
						? `<div class="qz-figure">${item.images!
								.map((src) => `<img src="${esc(src)}" alt="" loading="lazy">`)
								.join('')}<p class="qz-small">図表を含む問題のため、問題冊子の該当部分を画像で表示しています。下のボタンで番号を選んでください。</p></div>
							<p class="qz-sr">${esc(item.stem)}</p>`
						: `<p class="qz-stem">${esc(item.stem)}</p>${statements}`
				}
				${
					item.needsReview
						? `<p class="qz-warn">この問題には図や表があり、文字だけでは正しく表示できていない可能性があります。${
								item.pdfUrl ? `<a href="${esc(item.pdfUrl)}" target="_blank" rel="noopener">元の PDF</a> で確認してください。` : ''
							}</p>`
						: ''
				}
				<ol class="qz-choices ${figure ? 'qz-choices-row' : ''}">${choices}</ol>
				${feedback}
				${item.source ? `<p class="qz-source">${esc(item.source)}</p>` : ''}
			</article>
			<div class="qz-nav">
				<button type="button" class="qz-btn" data-go="${this.idx - 1}" ${this.idx === 0 ? 'disabled' : ''}>← 前へ</button>
				${
					!this.finished && this.opts.mode === 'exam'
						? '<button type="button" class="qz-btn qz-primary" data-finish>採点する</button>'
						: ''
				}
				<button type="button" class="qz-btn" data-go="${this.idx + 1}" ${this.idx === total - 1 ? 'disabled' : ''}>次へ →</button>
			</div>
			<details class="qz-griddetails" ${total <= 60 ? 'open' : ''}>
				<summary>問題一覧</summary>
				<div class="qz-grid">${grid}</div>
			</details>
			${summary}
		`;

		this.root.querySelectorAll<HTMLButtonElement>('[data-n]').forEach((b) =>
			b.addEventListener('click', () => this.choose(Number(b.dataset.n))),
		);
		this.root.querySelectorAll<HTMLButtonElement>('[data-go]').forEach((b) =>
			b.addEventListener('click', () => this.go(Number(b.dataset.go))),
		);
		this.root.querySelector('[data-finish]')?.addEventListener('click', () => this.finish());
		this.root.querySelector('[data-retry-wrong]')?.addEventListener('click', () => this.retryWrong());
		if (this.timer) this.tick();
	}

	private summary(correct: number) {
		const total = this.items.length;
		const byCat = new Map<string, { label: string; ok: number; n: number }>();
		this.items.forEach((it, i) => {
			const e = byCat.get(it.category) ?? { label: it.categoryLabel, ok: 0, n: 0 };
			e.n += 1;
			if (this.status(i) === 'correct') e.ok += 1;
			byCat.set(it.category, e);
		});
		const rows = [...byCat.values()]
			.map((e) => `<tr><td>${esc(e.label)}</td><td>${e.ok} / ${e.n}</td><td>${Math.round((e.ok / e.n) * 100)}%</td></tr>`)
			.join('');
		const pm = this.opts.passMark;
		const judge =
			pm
				? `<p class="qz-judge ${correct >= pm ? 'is-ok' : 'is-ng'}">${correct >= pm ? '合格ライン到達' : '合格ラインまであと ' + (pm - correct) + ' 問'}（この年度の合格基準点：${pm}問）</p>`
				: '';
		const wrong = this.items.filter((_, i) => this.status(i) !== 'correct').length;
		return `<section class="qz-summary">
			<h2>結果</h2>
			<p class="qz-score">${correct} / ${total} 問正解（${Math.round((correct / total) * 100)}%）</p>
			${judge}
			<table><thead><tr><th>分野</th><th>正解</th><th>正答率</th></tr></thead><tbody>${rows}</tbody></table>
			${wrong ? `<button type="button" class="qz-btn qz-primary" data-retry-wrong>間違えた ${wrong} 問だけ解き直す</button>` : ''}
		</section>`;
	}

	private retryWrong() {
		const wrong = this.items.filter((_, i) => this.status(i) !== 'correct');
		new QuizApp(this.root, wrong, { ...this.opts, mode: 'practice', passMark: null });
	}
}

export function shuffle<T>(arr: T[]): T[] {
	const a = arr.slice();
	for (let i = a.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1));
		[a[i], a[j]] = [a[j], a[i]];
	}
	return a;
}
