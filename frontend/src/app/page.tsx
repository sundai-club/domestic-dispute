import Link from 'next/link'
import { ArrowRight, Flame } from 'lucide-react'

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-500 via-red-500 to-pink-500 text-white">
      <div className="container mx-auto px-4 py-16">
        <nav className="flex justify-between items-center mb-16">
          <div className="text-2xl font-bold flex items-center">
            <Flame className="mr-2" />
            homewrecker.ai
          </div>
        </nav>
        <main className="flex flex-col lg:flex-row items-center justify-between">
          <div className="lg:w-1/2 mb-12 lg:mb-0">
            <h1 className="text-5xl lg:text-7xl font-extrabold mb-6 leading-tight">
            Use Textual Analysis to Determine Who is <span className="text-yellow-300">Sleeping on the Couch Tonight</span>
            </h1>
            <p className="text-xl mb-8">
              Upload your heated conversations and let our AI determine who's right. No more endless arguments!
            </p>
            <Link
              href="/dashboard"
              className="inline-flex items-center bg-yellow-400 text-red-700 px-8 py-4 rounded-full text-xl font-bold hover:bg-yellow-300 transition-colors"
            >
              Fuck it, let's go
              <ArrowRight className="ml-2" />
            </Link>
          </div>
          <div className="lg:w-1/2 relative">
            <img
              src="/couple-fighting.gif?height=400&width=400"
              alt="Couple arguing"
              className="relative z-10 rounded-lg shadow-2xl transform -rotate-3 hover:rotate-0 transition-transform duration-300"
            />
          </div>
        </main>
      </div>
    </div>
  )
}