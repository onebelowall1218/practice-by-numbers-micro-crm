import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { useAddInteraction } from "@/api/hooks";
import type { Contact, InteractionType } from "@/api/types";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";

const TYPES: InteractionType[] = ["email", "call", "meeting", "note"];
const NO_CONTACT = "__none__";

interface Props {
  customerId: string;
  contacts: Contact[];
  today: string;
  onAnalyzing: (analyzing: boolean) => void;
}

/** Log a new interaction. Raw notes are saved first; the AI then refreshes the whole analysis. */
export function AddInteractionDialog({ customerId, contacts, today, onAnalyzing }: Props) {
  const [open, setOpen] = useState(false);
  const [type, setType] = useState<InteractionType>("call");
  const [contactId, setContactId] = useState<string>(contacts[0]?.id ?? NO_CONTACT);
  const [occurredAt, setOccurredAt] = useState(today);
  const [notes, setNotes] = useState("");
  const mutation = useAddInteraction(customerId);

  function submit() {
    onAnalyzing(true);
    setOpen(false);
    mutation.mutate(
      {
        type,
        contact_id: contactId === NO_CONTACT ? null : contactId,
        occurred_at: occurredAt || null,
        notes,
      },
      {
        onSuccess: () => {
          toast.success("Interaction saved. Analysis updated.");
          setNotes("");
        },
        onError: (error) => toast.error(`Could not save interaction: ${error.message}`),
        onSettled: () => onAnalyzing(false),
      },
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button>
          <Plus className="size-4" /> Add interaction
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Log an interaction</DialogTitle>
          <DialogDescription>
            Paste notes or a transcript. The AI will summarise it and update the priority, next
            action and follow-up date.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4">
          <div className="grid grid-cols-2 gap-3">
            <label className="grid gap-1.5 text-sm">
              Type
              <Select value={type} onValueChange={(value) => setType(value as InteractionType)}>
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TYPES.map((option) => (
                    <SelectItem key={option} value={option} className="capitalize">
                      {option}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </label>
            <label className="grid gap-1.5 text-sm">
              Date
              <Input type="date" value={occurredAt} max={today} onChange={(e) => setOccurredAt(e.target.value)} />
            </label>
          </div>
          <label className="grid gap-1.5 text-sm">
            Contact
            <Select value={contactId} onValueChange={setContactId}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {contacts.map((contact) => (
                  <SelectItem key={contact.id} value={contact.id}>
                    {contact.name} · {contact.role}
                  </SelectItem>
                ))}
                <SelectItem value={NO_CONTACT}>No specific contact</SelectItem>
              </SelectContent>
            </Select>
          </label>
          <label className="grid gap-1.5 text-sm">
            Notes
            <Textarea
              rows={6}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Sarah called back: partners approved the proposal. She wants to start on Oct 1 and asked about staff training."
            />
          </label>
        </div>
        <DialogFooter>
          <Button variant="ghost" onClick={() => setOpen(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={notes.trim().length < 3 || mutation.isPending}>
            Save and analyze
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
