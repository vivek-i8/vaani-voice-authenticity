import { useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogTitle,
} from "@/components/ui/dialog";

interface ManusDialogProps {
  title?: string;
  logo?: string;
  open?: boolean;
  onLogin: () => void;
  onOpenChange?: (open: boolean) => void;
  onClose?: () => void;
}

export function ManusDialog({
  title,
  logo,
  open = false,
  onLogin,
  onOpenChange,
  onClose,
}: ManusDialogProps) {
  const [internalOpen, setInternalOpen] = useState(open);

  useEffect(() => {
    if (!onOpenChange) {
      setInternalOpen(open);
    }
  }, [open, onOpenChange]);

  const handleOpenChange = (nextOpen: boolean) => {
    if (onOpenChange) {
      onOpenChange(nextOpen);
    } else {
      setInternalOpen(nextOpen);
    }

    if (!nextOpen) {
      onClose?.();
    }
  };

  return (
    <Dialog
      open={onOpenChange ? open : internalOpen}
      onOpenChange={handleOpenChange}
    >
      <DialogContent className="w-full max-w-sm bg-card text-card-foreground rounded-2xl border border-white/10 p-0 gap-0 text-center shadow-xl">
        <div className="flex flex-col items-center gap-3 p-6 pt-10">
          {logo ? (
            <div className="w-16 h-16 bg-background/70 rounded-xl border border-white/15 flex items-center justify-center">
              <img src={logo} alt="Dialog graphic" className="w-10 h-10 rounded-md" />
            </div>
          ) : null}

          {/* Title and subtitle */}
          {title ? (
            <DialogTitle className="text-xl font-semibold text-white leading-tight">
              {title}
            </DialogTitle>
          ) : null}
          <DialogDescription className="text-sm text-gray-300 leading-relaxed">
            Please login with Manus to continue
          </DialogDescription>
        </div>

        <DialogFooter className="px-6 pb-6">
          {/* Login button */}
          <Button
            onClick={onLogin}
            className="w-full h-11 rounded-xl bg-teal-500 text-slate-950 hover:bg-teal-400 text-sm font-semibold"
          >
            Login with Manus
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
