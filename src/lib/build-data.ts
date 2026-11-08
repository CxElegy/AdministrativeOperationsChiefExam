/** ビルド時に、問題データを「階・部屋」の形にまとめる */
import { getCollection } from 'astro:content';
import { CATEGORIES, ROOM_SIZE } from '../data/categories';
import type { Question } from '../content.config';
import type { AppData, Exam, Floor, QItem } from './types';

const BASE = import.meta.env.BASE_URL.replace(/\/?$/, '/');
export const url = (p: string) => BASE + p.replace(/^\//, '');

/** 令和8年4月施行の区分所有法等の改正の影響を受けやすい分野 */
const AMENDED_CATS = new Set(['kubun', 'kiyaku']);

function toItem(id: string, set: string, q: Question, pdf?: string): QItem {
	return {
		id,
		set,
		no: q.no,
		cat: q.category,
		stem: q.stem,
		statements: q.statements,
		choices: q.choices,
		answer: q.answer,
		explanation: q.explanation,
		choiceNotes: q.choiceNotes,
		statementNotes: q.statementNotes,
		law: q.law,
		amendment: q.amendment,
		needsCheck: q.needsCheck,
		oldLaw: !!pdf && AMENDED_CATS.has(q.category) && !q.choiceNotes,
		source: q.source,
		images: q.images?.map((p) => url(p)),
		pdf,
	};
}

export async function getAppData(): Promise<AppData> {
	const exams = (await getCollection('kakomon')).map((e) => e.data).sort((a, b) => b.year - a.year);
	const drills = (await getCollection('drills'))
		.map((d) => ({ id: d.id, ...d.data }))
		.sort((a, b) => a.order - b.order);

	const questions: Record<string, QItem> = {};
	const byCat: Record<string, string[]> = Object.fromEntries(CATEGORIES.map((c) => [c.id, []]));

	// オリジナル問題を先に、その後に過去問（新しい年度から）
	for (const d of drills) {
		for (const q of d.questions) {
			const id = `drill-${d.id}-${q.no}`;
			questions[id] = toItem(id, d.title, q);
			byCat[q.category].push(id);
		}
	}
	const examList: Exam[] = [];
	for (const e of exams) {
		const qids: string[] = [];
		for (const q of e.questions) {
			const id = `${e.id}-${q.no}`;
			questions[id] = toItem(id, e.label, q, e.sourceUrl);
			byCat[q.category].push(id);
			qids.push(id);
		}
		examList.push({
			id: e.id,
			label: e.label,
			year: e.year,
			passMark: e.passMark ?? null,
			passMarkExempt: e.passMarkExempt ?? null,
			qids,
			pdf: e.sourceUrl,
		});
	}

	const floors: Floor[] = CATEGORIES.map((c, i) => {
		const ids = byCat[c.id];
		const rooms = [];
		for (let k = 0; k * ROOM_SIZE < ids.length; k++) {
			rooms.push({ id: `${c.id}-${k + 1}`, no: (i + 1) * 100 + k + 1, qids: ids.slice(k * ROOM_SIZE, (k + 1) * ROOM_SIZE) });
		}
		return { id: c.id, floor: i + 1, label: c.label, short: c.short, rooms };
	});

	return { floors, questions, exams: examList, examDay: '2026-12-06', base: BASE };
}
