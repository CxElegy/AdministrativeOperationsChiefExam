import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { CATEGORY_IDS } from './data/categories';

/** 1問分のデータ。過去問とオリジナル問題（ドリル）で共通。 */
const question = z.object({
	/** 問題番号（年度内・ドリル内で一意） */
	no: z.number().int().positive(),
	/** 分野。src/data/categories.ts の id */
	category: z.enum(CATEGORY_IDS),
	/** 問題文 */
	stem: z.string(),
	/** ア・イ・ウ…の記述（組合せ問題・個数問題のとき） */
	statements: z.array(z.object({ label: z.string(), text: z.string() })).optional(),
	/** 選択肢。4択なら4つ、○×なら ["正しい", "誤り"] */
	choices: z.array(z.string()).min(2),
	/** 正解の選択肢番号（1始まり）。複数正解は複数書く */
	answer: z.array(z.number().int().positive()).min(1),

	/** 解説：この問題のポイント */
	explanation: z.string().optional(),
	/** 解説：選択肢ごとの「なぜ正しい／なぜ違う」。choices と同じ順番 */
	choiceNotes: z.array(z.string()).optional(),
	/** 解説：ア〜エの記述ごとの正誤と理由 */
	statementNotes: z.array(z.object({ label: z.string(), correct: z.boolean(), note: z.string() })).optional(),
	/** 解説：根拠条文など */
	law: z.string().optional(),
	/** 令和8年4月施行の法改正などで結論が変わりうる場合の注意 */
	amendment: z.string().optional(),
	/** 解説の中で、まだ確認が必要な点（サイト上では「確認中」と表示） */
	needsCheck: z.string().optional(),

	/** 出典表示 */
	source: z.string().optional(),
	/** 図表の画像（public/ からのパス）。あれば問題文の代わりに画像を表示する */
	images: z.array(z.string()).optional(),
	needsReview: z.boolean().optional(),
	/** 手で修正済み（取り込みスクリプトで上書きしない） */
	manual: z.boolean().optional(),
	categoryLocked: z.boolean().optional(),
	tags: z.array(z.string()).optional(),
});

export type Question = z.infer<typeof question>;

export const collections = {
	// 読み物（試験ガイド・ノート）: src/content/guide 以下の .md
	guide: defineCollection({
		loader: glob({ pattern: '**/*.md', base: './src/content/guide' }),
		schema: z.object({
			title: z.string(),
			description: z.string().optional(),
			order: z.number().default(100),
			category: z.string().optional(),
		}),
	}),

	/** 過去問（年度ごとに 1 ファイル）: src/data/kakomon/rNN.json */
	kakomon: defineCollection({
		loader: glob({ pattern: '*.json', base: './src/data/kakomon' }),
		schema: z.object({
			id: z.string(),
			year: z.number(),
			label: z.string(),
			examDate: z.string().nullable().optional(),
			passMark: z.number().nullable().optional(),
			passMarkExempt: z.number().nullable().optional(),
			examinees: z.number().optional(),
			passers: z.number().optional(),
			sourceUrl: z.string().url(),
			questions: z.array(question),
		}),
	}),

	/** オリジナル問題（○×など）: src/data/drills/*.json。各分野の階の最初の部屋に入る */
	drills: defineCollection({
		loader: glob({ pattern: '*.json', base: './src/data/drills' }),
		schema: z.object({
			title: z.string(),
			description: z.string().optional(),
			order: z.number().default(100),
			questions: z.array(question),
		}),
	}),
};
