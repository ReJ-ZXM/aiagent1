import type { TripPlan } from '../../types'
import DayPlanCard from './DayPlanCard'

interface Props {
  plan: TripPlan
}

export default function ItineraryCard({ plan }: Props) {
  if (!plan?.days) return null

  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-bold flex items-center gap-2 mb-3">
        <span>🗺️</span> 行程详情
      </h3>
      <div className="space-y-4">
        {plan.days.map((day) => (
          <DayPlanCard key={day.day_number} day={day} />
        ))}
      </div>
    </div>
  )
}
