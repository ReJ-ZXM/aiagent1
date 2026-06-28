import type { TripPlan } from '../../types'
import DayPlanCard from './DayPlanCard'

interface Props { plan: TripPlan }

export default function ItineraryCard({ plan }: Props) {
  if (!plan?.days) return null

  return (
    <div className="card-travel p-4">
      <div className="flex items-center gap-2 mb-4">
        <span className="text-lg">🗺️</span>
        <span className="text-sm font-bold text-gray-700">
          行程详情 · {plan.days.length}天{plan.days.length > 1 ? '' : ''}
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
