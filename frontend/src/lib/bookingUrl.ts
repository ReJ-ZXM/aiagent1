/**
 * 预订链接生成工具
 * 跳转至各平台官网主页（确保 100% 可用）
 */

/** 12306 官网 — 火车票预订 */
export function get12306Url(): string {
  return 'https://www.12306.cn/'
}

/** 携程官网首页 */
export function getCtripUrl(): string {
  return 'https://www.ctrip.com/'
}

/** 携程酒店首页 */
export function getHotelHomeUrl(): string {
  return 'https://hotels.ctrip.com/'
}

/** 携程机票首页 */
export function getFlightHomeUrl(): string {
  return 'https://flights.ctrip.com/'
}

/** 携程门票/景点首页 */
export function getAttractionHomeUrl(): string {
  return 'https://you.ctrip.com/'
}

/** 大众点评首页 — 美食/餐厅 */
export function getDianpingUrl(): string {
  return 'https://www.dianping.com/'
}

/** 美团酒店首页 */
export function getMeituanHotelUrl(): string {
  return 'https://hotel.meituan.com/'
}

/** 根据交通类型获取预订平台链接 */
export function getTransportBookingUrl(
  type: string,
): { url: string; label: string; platform: string } {
  const isFlight = type.includes('飞机') || type.includes('航班') || type.includes('航空') || type.includes('flight')
  if (isFlight) {
    return {
      url: getFlightHomeUrl(),
      label: '预订机票',
      platform: '携程',
    }
  }
  return {
    url: get12306Url(),
    label: '预订车票',
    platform: '12306',
  }
}
