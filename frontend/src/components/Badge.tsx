import type { ReactNode } from 'react'

type Props = { variant?: 'outline' | 'filled' | 'dashed' | 'success'; children: ReactNode }

/** Selo dos wireframes: contorno, preenchido, tracejado ou sucesso. */
export default function Badge({ variant = 'outline', children }: Props) {
  return <span className={`badge badge-${variant}`}>{children}</span>
}
