/**
 * 出題分野 ＝ マンションの「階」。
 * 並び順が 1F → 8F。過去問 JSON の "category" はこの id を使う（william/build.py がこのファイルを読む）。
 */
export const CATEGORIES = [
	{ id: 'tekiseika', label: 'マンション管理適正化法', short: '適正化法' },
	{ id: 'kaikei', label: '管理組合の会計・税務', short: '会計' },
	{ id: 'itaku', label: '標準管理委託契約書', short: '委託契約' },
	{ id: 'minpo', label: '民法・借地借家法等', short: '民法' },
	{ id: 'kubun', label: '区分所有法等', short: '区分所有法' },
	{ id: 'kiyaku', label: '標準管理規約', short: '管理規約' },
	{ id: 'kenchiku', label: '建築・設備・維持修繕', short: '建築設備' },
	{ id: 'sonota', label: 'その他の法令・実務', short: 'その他' },
] as const;

export const CATEGORY_IDS = CATEGORIES.map((c) => c.id) as unknown as [
	(typeof CATEGORIES)[number]['id'],
	...(typeof CATEGORIES)[number]['id'][],
];

export type CategoryId = (typeof CATEGORIES)[number]['id'];

export const categoryLabel = (id: string) => CATEGORIES.find((c) => c.id === id)?.label ?? id;

