"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Breadcrumb } from "@/components/shared/breadcrumb";
import { ArrowLeft } from "lucide-react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  showBack?: boolean;
  backUrl?: string;
  action?: React.ReactNode;
}

export function PageHeader({ 
  title, 
  subtitle, 
  showBack = true, 
  backUrl,
  action 
}: PageHeaderProps) {
  const router = useRouter();

  const handleBack = () => {
    if (backUrl) {
      router.push(backUrl);
    } else {
      router.back();
    }
  };

  return (
    <header className="bg-white border-b sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 lg:px-8 py-4">
        <Breadcrumb />
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            {showBack && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleBack}
                className="flex-shrink-0"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            <div>
              <h1 className="text-xl lg:text-2xl font-bold">{title}</h1>
              {subtitle && <p className="text-sm text-slate-600 mt-1">{subtitle}</p>}
            </div>
          </div>
          {action && <div className="flex-shrink-0">{action}</div>}
        </div>
      </div>
    </header>
  );
}
