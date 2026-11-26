export type Role = 'customer' | 'product_owner' | 'developer' | 'project_manager'

export type User = {
  id: number
  username: string
  name: string
  role: Role
  role_label: string
  workspace: { id: number; name: string }
}

export type Category = { id: number; name: string }

export type RequestStatus =
  | 'submitted'
  | 'under_review'
  | 'approved'
  | 'rejected'
  | 'planned'
  | 'in_progress'
  | 'released'

export type RequestSummary = {
  id: number
  key: string
  title: string
  category: Category
  tags: string[]
  status: RequestStatus
  status_label: string
  votes: number
  voted: boolean
  my_role: 'created' | 'voted' | null
  author_name: string
  created_at: string
  updated_at: string
}

export type Comment = {
  id: number
  author_name: string
  author_role: string
  body: string
  is_decision: boolean
  created_at: string
}

export type RequestDetail = RequestSummary & {
  description: string
  importance: string
  version: number
  comments: Comment[]
  versions: { number: number; actor_name: string; summary: string; created_at: string }[]
  assessment: { impact: number | null; effort: number | null } | null
  can_assess: boolean
  next_statuses: { value: RequestStatus; label: string }[]
}

export type Page<T> = { count: number; next: string | null; previous: string | null; results: T[] }

export type PriorityRow = {
  id: number
  key: string
  title: string
  category: string
  category_id: number
  votes: number
  impact: number | null
  effort: number | null
  score: number | null
  manual: boolean
  manual_rank: number | null
  override_reason: string
}

export type Suggestion = {
  basis: string
  items: { id: number; key: string; title: string; reason: string }[]
}

export type PublicRoadmap = Record<
  'planned' | 'in_progress' | 'released',
  { id: number; title: string; category: string }[]
>

export type NotificationKind = 'mention' | 'status' | 'decision'

export type AppNotification = {
  id: number
  kind: NotificationKind
  kind_label: string
  message: string
  actor_name: string
  request_id: number
  read: boolean
  created_at: string
}

export type NotificationList = { unread: number; results: AppNotification[] }

export type Member = { username: string; name: string; role_label: string }
