import zh from './zh'
import en from './en'

type Locale = 'zh' | 'en'

let _locale: Locale = 'zh'

export function setLocale(lang: string): void {
  _locale = lang === 'en' ? 'en' : 'zh'
}

export function getLocale(): Locale {
  return _locale
}

/** Date-format locale string for toLocaleString() */
export function dateLocale(): string {
  return _locale === 'en' ? 'en-US' : 'zh-CN'
}

/**
 * Translate a key, with optional {placeholder} interpolation.
 * Falls back to the key itself if not found.
 */
export function t(key: string, params?: Record<string, string | number>): string {
  const dict = (_locale === 'en' ? en : zh) as Record<string, string>
  let msg = dict[key] ?? (zh as Record<string, string>)[key] ?? key
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      msg = msg.split(`{${k}}`).join(String(v))
    }
  }
  return msg
}
