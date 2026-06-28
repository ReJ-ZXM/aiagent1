import type { TripPlan } from '../../types'
import DayPlanCard from './DayPlanCard'

interface Props { plan: TripPlan }

export default function ItineraryCard({ plan }: Props) {
  if (!plan?.days) return null

  return (
    <div className="card-travel p-4">
      <div className="flex items-center gap-2 mb-4">
        <svg className="w-4 h-4 text-ocean-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.447 2.724A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
        <span className="text-sm font-bold text-gray-700">
          行程详情 · {plan.days.length} 天
        </span>
      </div>
      <div className="space-y-5">
        {plan.days.map((day) => (
          <DayPlanCard key={day.day_number} day={day} />
        ))}
      </div>
    </div>
  )
}
