import AppHeader from "../app-header";
import AppSidebar from "../app-sidebar";

interface MainWrapperProps {
  children: React.ReactNode;
}

const MainWrapper: React.FC<MainWrapperProps> = ({ children }) => {
  return (
    <div className="flex h-screen w-screen overflow-hidden">
      <AppSidebar />
      <div className="flex flex-col flex-grow overflow-hidden">
        <AppHeader />
        <main className="flex-grow overflow-y-auto py-6 p-6 md:pr-6 md:pl-[290px]">
          {children}
        </main>
      </div>
    </div>
  );
};

export default MainWrapper;
