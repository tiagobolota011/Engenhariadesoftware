type Props = { title: string }

/** Ecrã dos wireframes que ainda não está implementado. */
export default function ComingSoon({ title }: Props) {
  return (
    <>
      <h1 className="page-title">{title}</h1>
      <p className="empty">Em desenvolvimento — this screen is planned for the next sprint.</p>
    </>
  )
}
