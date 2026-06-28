import type { HotelInfo } from '../../types'

interface Props {
  hotel: HotelInfo
}

export default function HotelCard({ hotel }: Props) {
  if (!hotel) return null
  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-bold flex items-center gap-2 mb-3">
        <span>🏨</span> 住宿推荐
      </h3>
      <div className="flex justify-between items-start">
        <div>
          <p className="font-bold text-base">{hotel.name}</p>
          <p className="text-sm text-gray-500 mt-1">{hotel.address}</p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {hotel.highlights?.map((h, i) => (
              <span key={i} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
                {h}
              </span>
            ))}
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs text-gray-400">每晚</p>
          <p className="text-xl font-bold text-orange-600">¥{hotel.price_per_night}</p>
          <p className="text-xs text-gray-400 mt-1">
            {hotel.total_nights}晚共 ¥{hotel.total_price?.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  )
}
