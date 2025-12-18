'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface Country {
  id: number
  name: string
  code: string
  flag_url: string
  visa_types: VisaType[]
}

interface VisaType {
  id: number
  name: string
  code: string
  category: string
}

interface CricbuzzHeaderProps {
  countries: Country[]
}

export function CricbuzzHeader({ countries }: CricbuzzHeaderProps) {
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null)
  const [activeVisaType, setActiveVisaType] = useState<VisaType | null>(null)
  const [activeSubtab, setActiveSubtab] = useState<string>('interview')
  const router = useRouter()

  const handleCountrySelect = (country: Country) => {
    setSelectedCountry(country)
    setActiveVisaType(country.visa_types[0] || null)
    setActiveSubtab('interview')
  }

  const handleVisaTypeSelect = (visaType: VisaType) => {
    setActiveVisaType(visaType)
    setActiveSubtab('interview')
  }

  const handleSubtabSelect = (subtab: string) => {
    setActiveSubtab(subtab)
  }

  const subtabs = [
    { id: 'interview', label: 'Interview Experiences', href: '#interview' },
    { id: 'posts', label: 'Posts', href: '#posts' },
    { id: 'groups', label: 'Groups', href: '#groups' },
  ]

  return (
    <div className="w-full bg-white shadow-lg border-b">
      {/* Main Country Navigation */}
      <div className="border-b bg-gray-50">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center space-x-1 py-2 overflow-x-auto">
            {countries.map((country) => (
              <button
                key={country.id}
                onClick={() => handleCountrySelect(country)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
                  selectedCountry?.id === country.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100 border'
                }`}
              >
                <img
                  src={country.flag_url}
                  alt={country.name}
                  className="w-5 h-4 rounded-sm object-cover"
                />
                <span className="text-sm font-medium">{country.name}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Visa Types Navigation */}
      {selectedCountry && (
        <div className="border-b bg-blue-50">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center space-x-2 py-3 overflow-x-auto">
              <div className="flex items-center space-x-2 mr-4">
                <img
                  src={selectedCountry.flag_url}
                  alt={selectedCountry.name}
                  className="w-6 h-5 rounded-sm object-cover"
                />
                <span className="font-semibold text-gray-800">{selectedCountry.name}</span>
                <span className="text-gray-500">Visa Types</span>
              </div>
              {selectedCountry.visa_types.map((visaType) => (
                <button
                  key={visaType.id}
                  onClick={() => handleVisaTypeSelect(visaType)}
                  className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors font-medium ${
                    activeVisaType?.id === visaType.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-white text-gray-700 hover:bg-blue-100 border'
                  }`}
                >
                  {visaType.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Sub-navigation */}
      {activeVisaType && (
        <div className="bg-white">
          <div className="max-w-7xl mx-auto px-4">
            <div className="flex items-center space-x-8 py-3 border-b">
              {subtabs.map((subtab) => (
                <button
                  key={subtab.id}
                  onClick={() => handleSubtabSelect(subtab.id)}
                  className={`pb-3 px-1 border-b-2 transition-colors font-medium ${
                    activeSubtab === subtab.id
                      ? 'border-blue-600 text-blue-600'
                      : 'border-transparent text-gray-600 hover:text-gray-800'
                  }`}
                >
                  {subtab.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Content Area */}
      {activeVisaType && (
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="mb-4">
            <h1 className="text-2xl font-bold text-gray-900">
              {selectedCountry?.name} - {activeVisaType.name} {activeSubtab === 'interview' && 'Interview Experiences'}
              {activeSubtab === 'posts' && 'Posts'}
              {activeSubtab === 'groups' && 'Groups'}
            </h1>
            <p className="text-gray-600 mt-1">
              {activeSubtab === 'interview' && 'Share and read interview experiences for visa applications'}
              {activeSubtab === 'posts' && 'Community discussions and posts related to this visa type'}
              {activeSubtab === 'groups' && 'Join groups and communities for this visa type'}
            </p>
          </div>

          {/* Sample Content */}
          <div className="bg-gray-50 rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold text-gray-800 mb-2">
              {activeSubtab === 'interview' && 'Interview Experiences'}
              {activeSubtab === 'posts' && 'Community Posts'}
              {activeSubtab === 'groups' && 'Visa Groups'}
            </h3>
            <p className="text-gray-600">
              Content for {selectedCountry?.name} - {activeVisaType.name} {activeSubtab} section will be displayed here.
              This includes interview experiences, community posts, and group discussions.
            </p>
            <div className="mt-4">
              <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
                {activeSubtab === 'interview' && 'Share Your Experience'}
                {activeSubtab === 'posts' && 'Create Post'}
                {activeSubtab === 'groups' && 'Join Group'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}