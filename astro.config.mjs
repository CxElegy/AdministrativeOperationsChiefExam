// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

// GitHub Pages で公開する場合: https://<ユーザー名>.github.io/<リポジトリ名>/
// 独自ドメインやルート直下で公開する場合は SITE_BASE を "/" にする。
const base = process.env.SITE_BASE ?? '/AdministrativeOperationsChiefExam';

export default defineConfig({
	site: process.env.SITE_URL ?? 'https://cxelegy.github.io',
	base,
	trailingSlash: 'always',
	integrations: [
		starlight({
			title: '管業スタディ',
			description: '管理業務主任者試験の過去問演習と分野別ノート',
			defaultLocale: 'root',
			locales: { root: { label: '日本語', lang: 'ja' } },
			customCss: ['./src/styles/custom.css'],
			lastUpdated: false,
			sidebar: [
				{
					label: 'はじめに',
					items: [
						{ label: 'このサイトについて', link: '/' },
						{ label: '試験の概要', slug: 'exam' },
						{ label: '出題分野と学習の進め方', slug: 'scope' },
					],
				},
				{
					label: '問題演習',
					items: [
						{ label: '過去問（年度別）', link: '/kakomon/' },
						{ label: '分野別・ランダム演習', link: '/practice/' },
						{ label: '一問一答ドリル', link: '/drills/' },
						{ label: '学習記録', link: '/record/' },
					],
				},
				{
					label: '分野別ノート',
					items: [{ autogenerate: { directory: 'notes' } }],
				},
				{
					label: 'サイトの使い方',
					items: [{ label: 'コンテンツの追加方法', slug: 'contributing' }],
				},
			],
		}),
	],
});
