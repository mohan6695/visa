import { Hero } from '@/components/sections/Hero'
import { Features } from '@/components/sections/Features'
import { Countries } from '@/components/sections/Countries'
import { Community } from '@/components/sections/Community'
import { CTA } from '@/components/sections/CTA'

export default function HomePage() {
  return (
    <div className="flex flex-col">
      <Hero />
      <Features />
      <Countries />
      <Community />
      <CTA />
    </div>
  )
}