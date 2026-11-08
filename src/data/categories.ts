/**
 * 出題分野。過去問の JSON の "category" はこの id を使う。
 * 並び順はサイト上の表示順。
 */
export const CATEGORIES = [
	{ id: 'minpo', label: '民法・借地借家法等', short: '民法', note: 'notes/minpo' },
	{ id: 'itaku', label: '標準管理委託契約書', short: '委託契約', note: 'notes/itaku' },
	{ id: 'kaikei', label: '管理組合の会計・税務', short: '会計', note: 'notes/kaikei' },
	{ id: 'kenchiku', label: '建築・設備・維持修繕', short: '建築設備', note: 'notes/kenchiku' },
	{ id: 'kubun', label: '区分所有法等', short: '区分所有法', note: 'notes/kubun' },
	{ id: 'kiyaku', label: '標準管理規約', short: '管理規約', note: 'notes/kiyaku' },
	{ id: 'tekiseika', label: 'マンション管理適正化法', short: '適正化法', note: 'notes/tekiseika' },
	{ id: 'sonota', label: 'その他の法令・実務', short: 'その他', note: 'notes/sonota' },
] as const;

export const CATEGORY_IDS = CATEGORIES.map((c) => c.id) as unknown as [
	(typeof CATEGORIES)[number]['id'],
	...(typeof CATEGORIES)[number]['id'][],
];

export type CategoryId = (typeof CATEGORIES)[number]['id'];

export const categoryLabel = (id: string) => CATEGORIES.find((c) => c.id === id)?.label ?? id;
