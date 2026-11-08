/** ブラウザ側に渡す 1 問分のデータ */
export interface QuizItem {
	/** 記録用の一意な ID（例: "r07-12", "drill-tekiseika-3"） */
	id: string;
	/** 年度やドリル名（例: "令和7年度"） */
	set: string;
	/** 年度・ドリル内の問題番号 */
	no: number;
	category: string;
	categoryLabel: string;
	stem: string;
	statements?: { label: string; text: string }[];
	choices: string[];
	answer: number[];
	explanation?: string;
	source?: string;
	pdfUrl?: string;
	/** 図表の画像 URL */
	images?: string[];
	needsReview?: boolean;
}

export interface QuizOptions {
	/** "practice": 1問ごとに正誤表示 / "exam": 最後にまとめて採点 */
	mode: 'practice' | 'exam';
	/** 本番モードの制限時間（分） */
	timeLimit?: number;
	/** 合格基準点（本番モードの判定に使う） */
	passMark?: number | null;
	title?: string;
}
