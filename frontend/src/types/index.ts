// === 行程相关类型 ===

export interface TransportLeg {
  type: string
  number: string
  from: string
  to: string
  departure: string
  arrival: string
  price: number
}

export interface HotelInfo {
  name: string
  address: string
  price_per_night: number
  total_nights: number
  total_price: number
  highlights: string[]
}

export interface TripItem {
  type: 'transport' | 'hotel' | 'attraction' | 'meal'
  title: string
  start?: string
  end?: string
  description: string
  cost: number
}

export interface DayPlan {
  day_number: number
  date: string
  title: string
  items: TripItem[]
}

export interface BudgetBreakdown {
  transport: number
  hotel: number
  attractions: number
  meals: number
  total: number
  remaining: number
}

export interface TripPlan {
  summary: string
  transport?: {
    to: TransportLeg
    back: TransportLeg
  }
  hotel?: HotelInfo
  days: DayPlan[]
  budget_breakdown: BudgetBreakdown
}

// === 消息相关类型 ===

export type ContentType = 'text' | 'voice' | 'card'

export interface SSECardData {
  type: 'itinerary' | 'transport' | 'hotel'
  data: TripPlan
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  content_type: ContentType
  cards?: SSECardData[]
  created_at: string
}
