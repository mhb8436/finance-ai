'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  Home,
  MessageSquare,
  Database,
  Star,
  FileText,
  TrendingUp,
  Youtube,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  Menu,
  BarChart3,
  Building2,
} from 'lucide-react'

interface SubNavItem {
  href: string
  label: string
  icon: React.ElementType
}

interface NavItem {
  href: string
  label: string
  icon: React.ElementType
  description?: string
  subItems?: SubNavItem[]
}

const navItems: NavItem[] = [
  { href: '/', label: '홈', icon: Home, description: '대시보드' },
  { href: '/chat', label: 'AI 채팅', icon: MessageSquare, description: '주식 질의응답' },
  { href: '/knowledge', label: '지식 베이스', icon: Database, description: '문서 RAG' },
  { href: '/youtube', label: '유튜브 분석', icon: Youtube, description: '채널 분석' },
  {
    href: '/analysis',
    label: '고급 분석',
    icon: Star,
    description: '종합 분석',
    subItems: [
      { href: '/analysis', label: '종합 분석', icon: Star },
      { href: '/analysis/technical', label: '기술적 분석', icon: BarChart3 },
      { href: '/analysis/fundamental', label: '기본적 분석', icon: Building2 },
    ]
  },
  { href: '/research', label: '리서치', icon: FileText, description: '리포트 생성' },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [expandedMenus, setExpandedMenus] = useState<string[]>([])

  // Auto-expand menu if current path matches a subitem
  useEffect(() => {
    navItems.forEach(item => {
      if (item.subItems) {
        const isSubItemActive = item.subItems.some(sub =>
          sub.href === pathname || (sub.href !== '/analysis' && pathname.startsWith(sub.href))
        )
        if (isSubItemActive && !expandedMenus.includes(item.href)) {
          setExpandedMenus(prev => [...prev, item.href])
        }
      }
    })
  }, [pathname])

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname === href
  }

  const isParentActive = (item: NavItem) => {
    if (!item.subItems) return isActive(item.href)
    return item.subItems.some(sub => pathname === sub.href || (sub.href !== '/analysis' && pathname.startsWith(sub.href)))
  }

  const toggleExpanded = (href: string) => {
    setExpandedMenus(prev =>
      prev.includes(href)
        ? prev.filter(h => h !== href)
        : [...prev, href]
    )
  }

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-white dark:bg-gray-800 rounded-lg shadow-md"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile Overlay */}
      {mobileOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-50
          flex flex-col
          bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
          transition-all duration-300 ease-in-out
          ${collapsed ? 'w-16' : 'w-64'}
          ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
          {!collapsed && (
            <Link href="/" className="flex items-center gap-2">
              <TrendingUp className="w-8 h-8 text-primary-600" />
              <span className="text-xl font-bold">
                <span className="text-primary-600">Finance</span>AI
              </span>
            </Link>
          )}
          {collapsed && (
            <Link href="/" className="mx-auto">
              <TrendingUp className="w-8 h-8 text-primary-600" />
            </Link>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = isParentActive(item)
            const hasSubItems = item.subItems && item.subItems.length > 0
            const isExpanded = expandedMenus.includes(item.href)

            if (hasSubItems) {
              return (
                <div key={item.href}>
                  {/* Parent menu item with submenu */}
                  <button
                    onClick={() => toggleExpanded(item.href)}
                    className={`
                      w-full flex items-center gap-3 px-3 py-2.5 rounded-lg
                      transition-colors duration-150
                      ${active
                        ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                      }
                    `}
                    title={collapsed ? item.label : undefined}
                  >
                    <item.icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-primary-600' : ''}`} />
                    {!collapsed && (
                      <>
                        <div className="flex-1 min-w-0 text-left">
                          <div className="font-medium">{item.label}</div>
                          {item.description && (
                            <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                              {item.description}
                            </div>
                          )}
                        </div>
                        <ChevronDown
                          className={`w-4 h-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''}`}
                        />
                      </>
                    )}
                  </button>

                  {/* Submenu items */}
                  {!collapsed && isExpanded && (
                    <div className="ml-4 mt-1 space-y-1">
                      {item.subItems!.map((subItem) => {
                        const subActive = pathname === subItem.href ||
                          (subItem.href !== '/analysis' && pathname.startsWith(subItem.href))
                        return (
                          <Link
                            key={subItem.href}
                            href={subItem.href}
                            onClick={() => setMobileOpen(false)}
                            className={`
                              flex items-center gap-3 px-3 py-2 rounded-lg text-sm
                              transition-colors duration-150
                              ${subActive
                                ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                                : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                              }
                            `}
                          >
                            <subItem.icon className={`w-4 h-4 flex-shrink-0 ${subActive ? 'text-primary-600' : ''}`} />
                            <span>{subItem.label}</span>
                          </Link>
                        )
                      })}
                    </div>
                  )}
                </div>
              )
            }

            // Regular menu item without submenu
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileOpen(false)}
                className={`
                  flex items-center gap-3 px-3 py-2.5 rounded-lg
                  transition-colors duration-150
                  ${active
                    ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }
                `}
                title={collapsed ? item.label : undefined}
              >
                <item.icon className={`w-5 h-5 flex-shrink-0 ${active ? 'text-primary-600' : ''}`} />
                {!collapsed && (
                  <div className="flex-1 min-w-0">
                    <div className="font-medium">{item.label}</div>
                    {item.description && (
                      <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                        {item.description}
                      </div>
                    )}
                  </div>
                )}
              </Link>
            )
          })}
        </nav>

        {/* Collapse Button - Desktop Only */}
        <div className="hidden lg:block p-4 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            {collapsed ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <>
                <ChevronLeft className="w-5 h-5" />
                <span>접기</span>
              </>
            )}
          </button>
        </div>
      </aside>
    </>
  )
}
