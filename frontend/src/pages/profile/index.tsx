import MainTabBar from '@/components/MainTabBar'
import PlaceholderPage from '@/components/PlaceholderPage'

export default function ProfilePage() {
  return (
    <>
      <PlaceholderPage active={false} />
      <MainTabBar active='profile' />
    </>
  )
}
