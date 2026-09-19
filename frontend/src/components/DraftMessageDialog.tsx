import { Copy, MailPlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useDraftMessage } from "@/api/hooks";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";

/** Turns the recommended next action into an editable email the user can copy. Nothing is sent. */
export function DraftMessageDialog({ customerId }: { customerId: string }) {
  const [open, setOpen] = useState(false);
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const mutation = useDraftMessage(customerId);

  function openAndDraft() {
    setOpen(true);
    mutation.mutate(undefined, {
      onSuccess: (draft) => {
        setSubject(draft.subject);
        setBody(draft.body);
      },
      onError: (error) => toast.error(`Could not draft a message: ${error.message}`),
    });
  }

  async function copy() {
    await navigator.clipboard.writeText(`Subject: ${subject}\n\n${body}`);
    toast.success("Copied to clipboard");
  }

  return (
    <>
      <Button variant="outline" onClick={openAndDraft}>
        <MailPlus className="size-4" /> Draft follow-up
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Draft follow-up email</DialogTitle>
            <DialogDescription>
              Written from the timeline and the recommended next step. Edit freely, then copy.
            </DialogDescription>
          </DialogHeader>
          {mutation.isPending ? (
            <div className="space-y-3">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : (
            <div className="grid gap-3">
              <Input value={subject} onChange={(e) => setSubject(e.target.value)} />
              <Textarea rows={10} value={body} onChange={(e) => setBody(e.target.value)} />
            </div>
          )}
          <DialogFooter>
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Close
            </Button>
            <Button onClick={copy} disabled={mutation.isPending || !body}>
              <Copy className="size-4" /> Copy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
