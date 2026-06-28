import type { DayPlan, TripItem } from '../../types'
import { getAttractionHomeUrl, getDianpingUrl, getHotelHomeUrl, getTransportBookingUrl } from '../../lib/bookingUrl'

interface Props { day: DayPlan; city?: string }

const COLORS: Record<string, string> = {
  attraction: 'border-l-travel-400 bg-travel-50/50',
  meal: 'border-l-sunset-400 bg-sunset-50/50',
  transport: 'border-l-ocean-400 bg-ocean-50/50',
  hotel: 'border-l-purple-400 bg-purple-50/50',
}

export default function DayPlanCard({ day, city }: Props) {
  return (
    <div className="border-l-[3px] border-travel-300 pl-4 py-1">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-xs font-bold bg-travel-500 text-white rounded-lg px-2.5 py-1">
          DAY {day.day_number}
        </span>
        <span className="text-sm font-bold text-gray-700">{day.title}</span>
        <span className="text-xs text-gray-400">{day.date}</span>
      </div>
      <div className="space-y-2">
        {day.items?.map((item, i) => (
          <TimelineItem key={i} item={item} color={COLORS[item.type] || ''} />
        ))}
      </div>
    </div>
  )
}

function getItemBooking(item: TripItem): { url: string; label: string; platform: string } | null {
  switch (item.type) {
    case 'attraction':
      return { url: getAttractionHomeUrl(), label: '门票预订', platform: '携程' }
    case 'meal':
      return { url: getDianpingUrl(), label: '查看餐厅', platform: '大众点评' }
    case 'hotel':
      return { url: getHotelHomeUrl(), label: '预订酒店', platform: '携程' }
    case 'transport':
      return getTransportBookingUrl(item.title || '')
    default:
      return null
  }
}

function TimelineItem({ item, color }: { item: TripItem; color: string }) {
  const booking = getItemBooking(item)

  return (
    <div className={`flex gap-3 text-sm border border-gray-100 rounded-xl p-3 ${color}`}>
      <span className="shrink-0 w-2 h-2 mt-1.5 rounded-full bg-current opacity-40" />
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-start">
          <span className="font-medium text-gray-800 truncate">{item.title}</span>
          {item.cost > 0 && <span className="text-sunset-500 font-bold shrink-0 ml-2">¥{item.cost}</span>}
        </div>
        <div className="flex gap-2 text-xs text-gray-400 mt-1 flex-wrap items-center">
          {item.start && <span className="font-mono">{item.start}</span>}
          {item.start && item.end && <span>→</span>}
          {item.end && <span className="font-mono">{item.end}</span>}
          {item.description && <span className="truncate text-gray-500">· {item.description}</span>}
        </div>
        {booking && (
          <a
            href={booking.url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 mt-2 text-xs font-medium text-travel-600 hover:text-travel-700 bg-travel-50 hover:bg-travel-100 transition rounded-lg px-2.5 py-1 no-underline"
          >
            {booking.label}
            <span className="opacity-50 text-[10px]">@{booking.platform}</span>
          </a>
        )}
      </div>
    </div>
  )
}
