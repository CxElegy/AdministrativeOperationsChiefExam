/** ブラウザ側に渡す 1 問分のデータ */
export interface QItem {
	/** 記録用の一意な ID（例: "r07-12", "drill-tekiseika-basic-3"） */
	id: string;
	/** 年度・ドリル名（例: "令和7年度"） */
	set: string;
	no: number;
	cat: string;
	stem: string;
	statements?: { label: string; text: string }[];
	choices: string[];
	answer: number[];
	explanation?: string;
	choiceNotes?: string[];
	statementNotes?: { label: string; correct: boolean; note: string }[];
	law?: string;
	amendment?: string;
	needsCheck?: string;
	/** 改正前の法令に基づく出題であることの一般的な注意を出すか */
	oldLaw?: boolean;
	source?: string;
	images?: string[];
	pdf?: string;
}

export interface Room {
	id: string;
	/** 部屋番号（例: 101） */
	no: number;
	qids: string[];
}

export interface Floor {
	id: string;
	floor: number;
	label: string;
	short: string;
	rooms: Room[];
}

export interface Exam {
	id: string;
	label: string;
	year: number;
	passMark: number | null;
	passMarkExempt: number | null;
	qids: string[];
	pdf: string;
}

export interface AppData {
	floors: Floor[];
	questions: Record<string, QItem>;
	exams: Exam[];
	/** 本試験の日付（YYYY-MM-DD） */
	examDay: string;
	base: string;
}
