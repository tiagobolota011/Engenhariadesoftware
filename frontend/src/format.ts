const DAY = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })

/** "2 Oct 2026", como nos wireframes. */
export const formatDate = (iso: string) => DAY.format(new Date(iso))

export const plural = (count: number, word: string) => `${count} ${word}${count === 1 ? '' : 's'}`
