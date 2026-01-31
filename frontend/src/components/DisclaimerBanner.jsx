import { AlertTriangle, ExternalLink } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';

export default function DisclaimerBanner() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <div 
          className="px-4 py-2 bg-amber-500/10 border-t border-amber-500/20 cursor-pointer hover:bg-amber-500/20 transition-colors"
          data-testid="disclaimer-trigger"
        >
          <div className="flex items-center gap-2 text-amber-400 text-xs">
            <AlertTriangle className="h-3 w-3 flex-shrink-0" />
            <span className="font-medium">Important Disclaimer</span>
          </div>
        </div>
      </DialogTrigger>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="font-['Chivo'] flex items-center gap-2 text-amber-400">
            <AlertTriangle className="h-5 w-5" />
            Disclaimer for Brokers & Logistics Professionals
          </DialogTitle>
        </DialogHeader>
        <DialogDescription className="sr-only">
          Important legal disclaimer about the use of this calculation tool
        </DialogDescription>
        <div className="space-y-4 text-sm">
          <p className="text-muted-foreground leading-relaxed">
            This site is provided as a <strong className="text-foreground">secondary support tool</strong> to assist in the preliminary calculation of landed costs in The Bahamas. The results generated here <strong className="text-foreground">do not constitute legal or financial advice</strong>, nor are they binding upon the Government of The Bahamas or Bahamas Customs.
          </p>
          
          <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
            <h4 className="font-semibold text-amber-400 mb-2">User Responsibility</h4>
            <p className="text-muted-foreground">
              Users are responsible for verifying the correct HS Codes and Tariff Tiers for their specific imports. Final duty amounts are determined exclusively by Customs Officers at the time of entry.
            </p>
          </div>
          
          <div className="p-4 bg-primary/10 rounded-lg border border-primary/20">
            <h4 className="font-semibold text-primary mb-2">Official Verification</h4>
            <p className="text-muted-foreground mb-3">
              We recommend that all official queries be directed to the <strong className="text-foreground">Bahamas Customs Department</strong> for definitive classification.
            </p>
            <div className="flex flex-wrap gap-2 text-xs">
              <a 
                href="tel:+12423256550" 
                className="inline-flex items-center gap-1 px-2 py-1 bg-muted rounded hover:bg-muted/80"
              >
                📞 +1 (242) 325-6550
              </a>
              <a 
                href="mailto:customs@bahamas.gov.bs" 
                className="inline-flex items-center gap-1 px-2 py-1 bg-muted rounded hover:bg-muted/80"
              >
                ✉️ customs@bahamas.gov.bs
              </a>
              <a 
                href="https://www.bahamas.gov.bs/customs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2 py-1 bg-muted rounded hover:bg-muted/80"
              >
                <ExternalLink className="h-3 w-3" />
                Official Website
              </a>
            </div>
          </div>
          
          <p className="text-xs text-muted-foreground/70 text-center pt-2">
            By using this tool, you acknowledge and accept these terms.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
