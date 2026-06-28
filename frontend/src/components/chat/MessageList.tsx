import { useEffect, useRef } from 'react'
import type { Message } from '../../types'
import TransportCard from '../cards/TransportCard'
import HotelCard from '../cards/HotelCard'
import ItineraryCard from '../cards/ItineraryCard'

interface Props {
  messages: Message[]
  convId: string | null
}

export default function MessageList({ messages, convId }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center wave-bg">
        <div className="text-center animate-fade-in">
          <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-travel-500 to-ocean-500 flex items-center justify-center shadow-lg">
            <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-700 mb-3">旅行 AI 助手</h2>
          <p className="text-gray-400 text-lg mb-2">告诉我你想去哪里，剩下的交给我</p>
          <div className="flex flex-wrap justify-center gap-2 mt-6 text-sm text-gray-500">
            <span className="bg-white/80 backdrop-blur rounded-full px-4 py-1.5 shadow-sm">自然风光</span>
            <span className="bg-white/80 backdrop-blur rounded-full px-4 py-1.5 shadow-sm">人文历史</span>
            <span className="bg-white/80 backdrop-blur rounded-full px-4 py-1.5 shadow-sm">美食探店</span>
            <span className="bg-white/80 backdrop-blur rounded-full px-4 py-1.5 shadow-sm">城市购物</span>
          </div>
          <p className="text-xs text-gray-300 mt-8">试试说："明天去杭州3天，预算3000"</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-5 wave-bg">
      {messages.map((msg) => (
        <div
          key={msg.id}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-slide-up`}
        >
          {/* 助理头像 */}
          {msg.role === 'assistant' && (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-travel-400 to-ocean-400 flex items-center justify-center text-white shrink-0 mr-2 mt-1 shadow-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
          )}

          <div className="max-w-[78%]">
            {/* 只在没有卡片时显示文字气泡 */}
            {msg.content && !msg.cards?.length && (
              <div className={msg.role === 'user' ? 'bubble-user' : 'bubble-assistant'}>
                {msg.content}
              </div>
            )}
            {/* 加载动画 */}
            {!msg.content && !msg.cards?.length && msg.role === 'assistant' && (
              <div className="bubble-assistant">
                <div className="dot-typing">
                  <span /><span /><span />
                </div>
              </div>
            )}

            {/* 行程卡片 */}
            {msg.cards?.map((card, i) => (
              <div key={i} className="space-y-3 animate-slide-up" style={{ animationDelay: `${i * 0.1}s` }}>
                {card.type === 'itinerary' && card.data.summary && (
                  <div className="card-travel p-4 bg-gradient-to-br from-travel-50 to-ocean-50 border-0">
                    <div className="flex items-center gap-2 mb-2">
                      <svg className="w-4 h-4 text-travel-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-sm font-bold text-travel-700">方案概要</span>
                    </div>
                    <p className="text-sm text-gray-600 leading-relaxed">{card.data.summary}</p>
                  </div>
                )}
                {card.type === 'itinerary' && card.data.transport && (
                  <TransportCard transport={card.data.transport} />
                )}
                {card.type === 'itinerary' && card.data.hotel && (
                  <HotelCard hotel={card.data.hotel} />
                )}
                {card.type === 'itinerary' && (
                  <>
                    <ItineraryCard plan={card.data} />
                    {convId && (
                      <div className="flex justify-center mt-2">
                        <a
                          href={`/api/v1/trips/${convId}/export`}
                          className="inline-flex items-center gap-2 text-sm font-medium text-white bg-red-500 hover:bg-red-600 transition rounded-xl px-5 py-2.5 shadow-sm no-underline cursor-pointer"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                          </svg>
                          下载 PDF
                        </a>
                      </div>
                    )}
                  </>
                )}
                {card.type === 'itinerary' && card.data.budget_breakdown && (
                  <BudgetBar
                    breakdown={card.data.budget_breakdown}
                    budget={card.data.budget_breakdown.total + card.data.budget_breakdown.remaining}
                  />
                )}
              </div>
            ))}
          </div>

          {/* 用户头像 */}
          {msg.role === 'user' && (
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-sunset-400 to-sunset-500 flex items-center justify-center text-white shrink-0 ml-2 mt-1 shadow-sm">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

function BudgetBar({ breakdown, budget }: { breakdown: { total: number; remaining: number }; budget: number }) {
  const pct = budget > 0 ? Math.round((breakdown.total / budget) * 100) : 0
  const isOverBudget = pct > 80
  const barColor = isOverBudget ? 'from-sunset-400 to-red-400' : 'from-emerald-400 to-teal-400'

  return (
    <div className="card-travel p-4">
      <div className="flex justify-between items-center mb-3">
        <span className="text-sm font-bold text-gray-700">预算概览</span>
        <span className={`text-xs font-bold ${isOverBudget ? 'text-sunset-500' : 'text-emerald-500'}`}>
          {pct}% 已用
        </span>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-3 mb-3 overflow-hidden">
        <div
          className={`h-3 rounded-full bg-gradient-to-r ${barColor} transition-all duration-700 ease-out`}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-sm">
        <span className="font-bold text-gray-800">已用 ¥{breakdown.total.toLocaleString()}</span>
        <span className="text-gray-400">剩余 ¥{breakdown.remaining.toLocaleString()}</span>
      </div>
    </div>
  )
}
