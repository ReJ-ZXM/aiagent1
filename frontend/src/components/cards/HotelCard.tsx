import type { HotelInfo } from '../../types'
import { getHotelHomeUrl } from '../../lib/bookingUrl'

interface Props { hotel: HotelInfo }

export default function HotelCard({ hotel }: Props) {
  if (!hotel) return null

  return (
    <div className="card-travel p-4">
      <div className="flex items-center gap-2 mb-3">
        <svg className="w-4 h-4 text-sunset-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <span className="text-sm font-bold text-gray-700">住宿推荐</span>
      </div>
      <div className="flex justify-between items-start gap-3">
        <div className="flex-1 min-w-0">
          <p className="font-bold text-base text-gray-800 truncate">{hotel.name}</p>
          <p className="text-xs text-gray-400 mt-1 flex items-center gap-1">
            <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {hotel.address}
          </p>
          {hotel.highlights?.length > 0 && (
            <div className="flex gap-1.5 mt-2 flex-wrap">
              {hotel.highlights.map((h, i) => (
                <span key={i} className="text-xs bg-emerald-50 text-emerald-600 px-2.5 py-1 rounded-full font-medium">
                  {h}
                </span>
              ))}
            </div>
          )}
        </div>
        <div className="text-right shrink-0 flex flex-col items-end gap-2">
          <div>
            <p className="text-xs text-gray-400">每晚</p>
            <p className="text-2xl font-bold text-sunset-500">¥{hotel.price_per_night}</p>
            <p className="text-xs text-gray-400 mt-0.5">
              {hotel.total_nights}晚共 <span className="font-bold text-gray-600">¥{hotel.total_price?.toLocaleString()}</span>
            </p>
          </div>
          <a
            href={getHotelHomeUrl()}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-white bg-sunset-500 hover:bg-sunset-600 transition rounded-lg px-3 py-1.5 no-underline inline-flex items-center gap-1"
          >
            预订酒店
            <span className="opacity-70 text-[10px]">@携程</span>
          </a>
        </div>
      </div>
    </div>
  )
}
