// @ts-check
import { defineConfig } from 'astro/config';

// GitHub Pages で公開する場合: https://<ユーザー名>.github.io/<リポジトリ名>/
// 独自ドメインやルート直下で公開する場合は SITE_BASE を "/" にする。
const base = process.env.SITE_BASE ?? '/AdministrativeOperationsChiefExam';

export default defineConfig({
	site: process.env.SITE_URL ?? 'https://cxelegy.github.io',
	base,
	trailingSlash: 'always',
});
