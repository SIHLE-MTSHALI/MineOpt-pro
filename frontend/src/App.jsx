import { useState, useEffect, useRef } from 'react'
import MineMap from './components/MineMap'
import ShiftPanel from './components/ShiftPanel'
import PlanningPage from './components/PlanningPage'
import NavButton from './components/NavButton'
import { Activity, Fuel, TrendingUp, Truck, Play, Square, Settings, Layers } from 'lucide-react'
import axios from 'axios'
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

function cn(...inputs) {
  return twMerge(clsx(inputs))
}

// KPI Card Component
const KPICard = ({ title, value, unit, icon: Icon, color }) => (
  <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 shadow-lg">
    <div className="flex justify-between items-start">
      <div>
        <p className="text-slate-400 text-sm font-medium">{title}</p>
        <h3 className="text-2xl font-bold text-white mt-1">
          {value} <span className="text-sm text-slate-500 font-normal">{unit}</span>
        </h3>
      </div>
      <div className={cn("p-2 rounded-lg", color)}>
        <Icon className="w-5 h-5 text-white" />
      </div>
    </div>
  </div>
)

export default function App() {
  const [simulationState, setSimulationState] = useState(null)
  const [isConnected, setIsConnected] = useState(false)
  const [isRunning, setIsRunning] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard') // 'dashboard' | 'planning'

  // Connection and WebSocket logic
  const wsRef = useRef(null)

  useEffect(() => {
    // Connect to WebSocket
    const ws = new WebSocket('ws://localhost:8000/simulation/ws')
    wsRef.current = ws

    ws.onopen = () => {
      console.log('Connected to simulation stream')
      setIsConnected(true)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setSimulationState(data)
    }

    ws.onclose = () => {
      setIsConnected(false)
    }

    return () => {
      ws.close()
    }
  }, [])

  const startSimulation = async () => {
    try {
      if (!simulationState) {
        const initRes = await axios.post('http://localhost:8000/simulation/init', {
          num_trucks: 15,
          num_shovels: 4
        })
        if (initRes.data.initial_state) {
          setSimulationState(initRes.data.initial_state)
        }
      }
      const startRes = await axios.post('http://localhost:8000/simulation/start')
      if (startRes.data.state) {
        setSimulationState(startRes.data.state)
      }
      setIsRunning(true)
    } catch (e) {
      console.error(e)
    }
  }

  const stopSimulation = async () => {
    try {
      await axios.post('http://localhost:8000/simulation/stop')
      setIsRunning(false)
    } catch (e) {
      console.error(e)
    }
  }

  // Derived metrics
  const trucks = simulationState?.trucks || []
  const shovels = simulationState?.shovels || []

  const activeTrucks = trucks.filter(t => t.status !== 'idle').length
  const utilization = trucks.length > 0 ? (activeTrucks / trucks.length) * 100 : 0

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 font-sans overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col">
        <div className="p-6">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            MineOpt
          </h1>
          <p className="text-xs text-slate-500 mt-1">Witbank Operations</p>
        </div>

        <nav className="flex-1 px-4 space-y-2 flex flex-col items-center pt-4">
          <NavButton icon={Activity} active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
          <NavButton icon={Layers} active={activeTab === 'planning'} onClick={() => setActiveTab('planning')} />
          <NavButton icon={Settings} active={activeTab === 'settings'} onClick={() => { }} />
        </nav>

        <div className="p-4 border-t border-slate-800">
          <div className="bg-slate-800/50 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-green-500" : "bg-red-500")} />
              <span className="text-xs font-medium text-slate-400">
                System: {isConnected ? 'Online' : 'Offline'}
              </span>
            </div>
            {isRunning ? (
              <button
                onClick={stopSimulation}
                className="w-full py-2 bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20 rounded-lg flex items-center justify-center gap-2 transition-all"
              >
                <Square size={16} fill="currentColor" /> Stop Sim
              </button>
            ) : (
              <button
                onClick={startSimulation}
                className="w-full py-2 bg-blue-500 text-white hover:bg-blue-600 rounded-lg flex items-center justify-center gap-2 transition-all shadow-lg shadow-blue-500/20"
              >
                <Play size={16} fill="currentColor" /> Start Sim
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-h-0">

        {/* Top KPIs */}
        {activeTab === 'dashboard' ? (
          <>
            <div className="h-auto p-6 grid grid-cols-4 gap-6 bg-slate-950/50 z-10">
              <KPICard
                title="Fleet Utilization"
                value={utilization.toFixed(1)}
                unit="%"
                icon={Activity}
                color="bg-blue-500/20"
              />
              <KPICard
                title="Production"
                value={simulationState?.total_production_tonnes?.toFixed(0) || 0}
                unit="t"
                icon={TrendingUp}
                color="bg-green-500/20"
              />
              <KPICard
                title="Fuel Consumed"
                value={simulationState?.total_fuel_consumed?.toFixed(0) || 0}
                unit="L"
                icon={Fuel}
                color="bg-orange-500/20"
              />
              <KPICard
                title="Active Trucks"
                value={activeTrucks}
                unit={`/ ${trucks.length}`}
                icon={Truck}
                color="bg-indigo-500/20"
              />
            </div>

            {/* Map Area */}
            <div className="flex-1 relative bg-slate-900 overflow-hidden m-6 mt-0 rounded-2xl border border-slate-800 shadow-2xl">
              {/* Map Overlay Info */}
              <div className="absolute top-4 right-4 z-[400] bg-slate-900/90 backdrop-blur border border-slate-700 p-4 rounded-xl text-sm">
                <p className="text-slate-400">Weather Condition</p>
                <p className="text-white font-medium capitalize flex items-center gap-2">
                  {simulationState?.current_weather || 'Unknown'}
                </p>
              </div>

              <MineMap
                trucks={trucks}
                shovels={shovels}
              />
            </div>
          </>
        ) : (
          <PlanningPage simulationState={simulationState} />
        )}

        {/* Shift Control Panel */}
        {simulationState && (
          <ShiftPanel
            shiftName={simulationState.current_shift}
            progress={simulationState.shift_progress_percent}
            production={simulationState.total_production_tonnes} // Ideally this should be shift production, but using total for now
            target={simulationState.shift_production_target}
          />
        )}
      </div>
    </div>
  )
}
