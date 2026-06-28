import { useEffect, useRef } from 'react'
import type { Message } from '../../types'
import TransportCard from '../cards/TransportCard'
import HotelCard from '../cards/HotelCard'
import ItineraryCard from '../cards/ItineraryCard'

interface Props {
  messages: Message[]
}

export default function MessageList({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-4xl mb-4">✈️</p>
          <p className="text-lg mb-2">告诉我你的旅行计划吧！</p>
          <p className="text-sm">例如："明天去杭州，7月2号回，预算5000"</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.map((msg) => (
        <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className="max-w-[80%]">
            {/* 只在没有卡片时显示文字气泡，避免与卡片内容重复 */}
            {msg.content && !msg.cards?.length && (
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white rounded-br-sm'
                    : 'bg-white border text-gray-800 rounded-bl-sm shadow-sm'
                }`}
              >
                {msg.content}
              </div>
            )}
            {/* 加载中动画：无内容且无卡片 */}
            {!msg.content && !msg.cards?.length && msg.role === 'assistant' && (
              <div className="bg-white border rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
                <span className="inline-flex gap-1">
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                  <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                </span>
              </div>
            )}

            {msg.cards?.map((card, i) => {
              if (card.type === 'itinerary') {
                const plan = card.data
                return (
                  <div key={i} className="mt-3 space-y-3">
                    {plan.summary && (
                      <div className="bg-white border rounded-xl p-3 shadow-sm text-sm text-gray-700">
                        {plan.summary}
                      </div>
                    )}
                    {plan.transport && <TransportCard transport={plan.transport} />}
                    {plan.hotel && <HotelCard hotel={plan.hotel} />}
                    <ItineraryCard plan={plan} />
                    {plan.budget_breakdown && (
                      <BudgetBar breakdown={plan.budget_breakdown} budget={plan.budget_breakdown.total + plan.budget_breakdown.remaining} />
                    )}
                  </div>
                )
              }
              return null
            })}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

function BudgetBar({ breakdown, budget }: { breakdown: { total: number; remaining: number }; budget: number }) {
  const pct = budget > 0 ? Math.round((breakdown.total / budget) * 100) : 0
  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm">
      <div className="flex justify-between text-sm mb-2">
        <span className="font-medium">💰 预算概览</span>
        <span className="text-gray-500">{pct}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
        <div
          className="bg-green-500 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-green-600 font-medium">已用 ¥{breakdown.total.toLocaleString()}</span>
        <span className="text-gray-400">剩余 ¥{breakdown.remaining.toLocaleString()}</span>
      </div>
    </div>
  )
}
