'use client'

import { useState } from 'react'

interface Country {
  id: number
  name: string
  code: string
  flag_url: string
  top_visas: VisaType[]
}

interface VisaType {
  name: string
  code: string
  category: string
}

// Sample data for demonstration
const SAMPLE_COUNTRIES = [
  {
    id: 1,
    name: "United States",
    code: "USA",
    flag_url: "https://flagcdn.com/w320/us.png",
    top_visas: [
      { name: "H-1B Visa", code: "H1B", category: "work" },
      { name: "H-4 Visa", code: "H4", category: "family" },
      { name: "F-1 Visa", code: "F1", category: "student" },
      { name: "J-1 Visa", code: "J1", category: "exchange" },
      { name: "O-1 Visa", code: "O1", category: "work" },
      { name: "EB-1 Visa", code: "EB1", category: "immigration" },
      { name: "EB-2 Visa", code: "EB2", category: "immigration" }
    ]
  },
  {
    id: 2,
    name: "Canada",
    code: "CAN",
    flag_url: "https://flagcdn.com/w320/ca.png",
    top_visas: [
      { name: "Express Entry", code: "EE", category: "immigration" },
      { name: "Provincial Nominee Program", code: "PNP", category: "immigration" },
      { name: "Work Permit", code: "WP", category: "work" },
      { name: "Study Permit", code: "SP", category: "student" },
      { name: "Family Sponsorship", code: "FS", category: "family" },
      { name: "Business Immigration", code: "BI", category: "business" },
      { name: "Atlantic Immigration", code: "AIP", category: "immigration" }
    ]
  },
  {
    id: 3,
    name: "United Kingdom",
    code: "GBR",
    flag_url: "https://flagcdn.com/w320/gb.png",
    top_visas: [
      { name: "Skilled Worker Visa", code: "SW", category: "work" },
      { name: "Student Visa", code: "STU", category: "student" },
      { name: "Global Talent Visa", code: "GT", category: "work" },
      { name: "Family Visa", code: "FAM", category: "family" },
      { name: "Graduate Route", code: "GR", category: "work" },
      { name: "Start-up Visa", code: "SU", category: "business" },
      { name: "Innovator Visa", code: "INN", category: "business" }
    ]
  },
  {
    id: 4,
    name: "Australia",
    code: "AUS",
    flag_url: "https://flagcdn.com/w320/au.png",
    top_visas: [
      { name: "Skilled Independent Visa", code: "189", category: "immigration" },
      { name: "Skilled Nominated Visa", code: "190", category: "immigration" },
      { name: "Temporary Skill Shortage", code: "TSS", category: "work" },
      { name: "Student Visa", code: "500", category: "student" },
      { name: "Partner Visa", code: "820/801", category: "family" },
      { name: "Employer Nomination Scheme", code: "186", category: "immigration" },
      { name: "Working Holiday Visa", code: "417", category: "work" }
    ]
  },
  {
    id: 5,
    name: "Germany",
    code: "DEU",
    flag_url: "https://flagcdn.com/w320/de.png",
    top_visas: [
      { name: "Blue Card", code: "BC", category: "work" },
      { name: "Student Visa", code: "STU", category: "student" },
      { name: "Job Seeker Visa", code: "JS", category: "work" },
      { name: "Family Reunification", code: "FR", category: "family" },
      { name: "EU Residence Permit", code: "EU", category: "immigration" },
      { name: "Entrepreneur Visa", code: "ENT", category: "business" },
      { name: "Research Visa", code: "RES", category: "work" }
    ]
  }
]

export function LandingPage() {
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null)
  const [activeVisaType, setActiveVisaType] = useState<VisaType | null>(null)
  const [activeSubtab, setActiveSubtab] = useState<string>('interview')

  const handleCountrySelect = (country: Country) => {
    setSelectedCountry(country)
    setActiveVisaType(country.top_visas[0] || null)
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
    { id: 'interview', label: 'Interview Experiences' },
    { id: 'posts', label: 'Posts' },
    { id: 'groups', label: 'Groups' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              Visa Platform
            </h1>
            <p className="text-xl md:text-2xl mb-8 opacity-90">
              Your Gateway to Global Travel and Immigration
            </p>
            <p className="text-lg opacity-80 max-w-3xl mx-auto">
              Get comprehensive visa information, connect with communities, 
              share experiences, and make your immigration journey successful.
            </p>
          </div>
        </div>
      </div>

      {/* Country Selection */}
      <div className="max-w-7xl mx-auto px-4 py-12">
        <div className="text-center mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Select Your Destination Country
          </h2>
          <p className="text-gray-600">
            Choose a country to explore visa types and connect with the community
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4 mb-12">
          {SAMPLE_COUNTRIES.map((country) => (
            <button
              key={country.id}
              onClick={() => handleCountrySelect(country)}
              className={`p-6 rounded-lg border-2 transition-all hover:shadow-lg ${
                selectedCountry?.id === country.id
                  ? 'border-blue-500 bg-blue-50 shadow-md'
                  : 'border-gray-200 bg-white hover:border-gray-300'
              }`}
            >
              <img
                src={country.flag_url}
                alt={country.name}
                className="w-16 h-12 mx-auto mb-3 rounded object-cover"
              />
              <h3 className="font-semibold text-gray-900">{country.name}</h3>
              <p className="text-sm text-gray-500 mt-1">
                {country.top_visas.length} visa types
              </p>
            </button>
          ))}
        </div>

        {/* Country Navigation */}
        {selectedCountry && (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Country Header */}
            <div className="bg-blue-600 text-white p-6">
              <div className="flex items-center space-x-4">
                <img
                  src={selectedCountry.flag_url}
                  alt={selectedCountry.name}
                  className="w-12 h-8 rounded object-cover"
                />
                <div>
                  <h2 className="text-2xl font-bold">{selectedCountry.name} Visa Information</h2>
                  <p className="opacity-90">Explore visa types and connect with the community</p>
                </div>
              </div>
            </div>

            {/* Visa Types */}
            <div className="p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Popular Visa Types</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-6">
                {selectedCountry.top_visas.map((visaType) => (
                  <button
                    key={visaType.code}
                    onClick={() => handleVisaTypeSelect(visaType)}
                    className={`p-4 rounded-lg border text-left transition-colors ${
                      activeVisaType?.code === visaType.code
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="font-medium text-gray-900">{visaType.name}</div>
                    <div className="text-sm text-gray-500 capitalize">{visaType.category}</div>
                  </button>
                ))}
              </div>

              {/* Sub-navigation */}
              {activeVisaType && (
                <div className="border-t pt-6">
                  <div className="flex space-x-1 mb-4">
                    {subtabs.map((subtab) => (
                      <button
                        key={subtab.id}
                        onClick={() => handleSubtabSelect(subtab.id)}
                        className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                          activeSubtab === subtab.id
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        {subtab.label}
                      </button>
                    ))}
                  </div>

                  {/* Content */}
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h4 className="text-xl font-semibold text-gray-900 mb-2">
                      {selectedCountry.name} - {activeVisaType.name}
                    </h4>
                    <h5 className="text-lg font-medium text-gray-700 mb-4">
                      {subtabs.find(s => s.id === activeSubtab)?.label}
                    </h5>
                    
                    <div className="text-center py-8">
                      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                      </div>
                      <p className="text-gray-600 mb-4">
                        Content for {subtabs.find(s => s.id === activeSubtab)?.label.toLowerCase()} will be displayed here.
                        This section will include community discussions, experiences, and group activities.
                      </p>
                      <button className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors">
                        {activeSubtab === 'interview' && 'Share Your Interview Experience'}
                        {activeSubtab === 'posts' && 'Create New Post'}
                        {activeSubtab === 'groups' && 'Join Related Groups'}
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Features Section */}
        {!selectedCountry && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
            <div className="text-center p-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Community Discussions</h3>
              <p className="text-gray-600">
                Connect with other travelers, share experiences, and get answers to your visa questions.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Interview Experiences</h3>
              <p className="text-gray-600">
                Read real interview experiences and preparation tips from successful applicants.
              </p>
            </div>

            <div className="text-center p-6">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Expert Groups</h3>
              <p className="text-gray-600">
                Join specialized groups for different visa types and get expert guidance.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}