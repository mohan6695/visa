"use client"

import { AdBanner } from './AdBanner'
import { AdSidebar } from './AdSidebar'
import { AdInFeed } from './AdInFeed'

export default function Ads() {
  return (
    <>
      {/* Top Banner Ad */}
      <AdBanner slotId="top-banner-ad" format="horizontal" className="my-4" />
      
      {/* Left Sidebar Ad */}
      <AdSidebar slotId="left-sidebar-ad" position="left" />
      
      {/* Right Sidebar Ad */}
      <AdSidebar slotId="right-sidebar-ad" position="right" />
    </>
  )
}
