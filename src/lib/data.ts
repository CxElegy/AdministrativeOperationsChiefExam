import { getCollection } from 'astro:content';
import { categoryLabel } from '../data/categories';
import type { QuizItem } from './types';

export async function getExams() {
	const exams = await getCollection('kakomon');
	return exams.map((e) => e.data).sort((a, b) => b.year - a.year);
}

export async function getDrills() {
	const drills = await getCollection('drills');
	return drills
		.map((d) => ({ id: d.id, ...d.data }))
		.sort((a, b) => a.order - b.order || a.title.localeCompare(b.title));
}

type Exam = Awaited<ReturnType<typeof getExams>>[number];
type Drill = Awaited<ReturnType<typeof getDrills>>[number];

export function examItems(exam: Exam): QuizItem[] {
	return exam.questions.map((q) => ({
		id: `${exam.id}-${q.no}`,
		set: exam.label,
		no: q.no,
		category: q.category,
		categoryLabel: categoryLabel(q.category),
		stem: q.stem,
		statements: q.statements,
		choices: q.choices,
		answer: q.answer,
		explanation: q.explanation,
		source: q.source,
		pdfUrl: exam.sourceUrl,
		images: q.images?.map((p) => url(p)),
		needsReview: q.needsReview,
	}));
}

export function drillItems(drill: Drill): QuizItem[] {
	return drill.questions.map((q) => ({
		id: `drill-${drill.id}-${q.no}`,
		set: drill.title,
		no: q.no,
		category: q.category,
		categoryLabel: categoryLabel(q.category),
		stem: q.stem,
		statements: q.statements,
		choices: q.choices,
		answer: q.answer,
		explanation: q.explanation,
		source: q.source,
		images: q.images?.map((p) => url(p)),
	}));
}

/** サイト内リンク（base を付ける） */
export const url = (path: string) => `${import.meta.env.BASE_URL.replace(/\/$/, '')}/${path.replace(/^\//, '')}`;
