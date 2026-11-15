import type { Role } from '../api/types'

const TEAM: Role[] = ['product_owner', 'developer', 'project_manager']
const EVERYONE: Role[] = ['customer', ...TEAM]

/** As nove entradas do menu dos wireframes e os papéis que as veem. */
export const NAV: { to: string; label: string; roles: Role[] }[] = [
  { to: '/requests', label: 'Requests', roles: EVERYONE },
  { to: '/my-requests', label: 'My Requests', roles: EVERYONE },
  { to: '/prioritization', label: 'Prioritization', roles: ['product_owner'] },
  { to: '/backlog', label: 'Backlog', roles: TEAM },
  { to: '/user-stories', label: 'User Stories', roles: ['product_owner', 'developer'] },
  { to: '/traceability', label: 'Traceability', roles: TEAM },
  { to: '/roadmap', label: 'Roadmap', roles: TEAM },
  { to: '/dashboard', label: 'Dashboard', roles: ['product_owner', 'project_manager'] },
  { to: '/notifications', label: 'Notifications', roles: EVERYONE },
]
