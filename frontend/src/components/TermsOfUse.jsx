import { AlertTriangle, Shield, ExternalLink } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';
import { Separator } from './ui/separator';

export default function TermsOfUse() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button 
          variant="ghost" 
          size="sm"
          className="gap-2 text-xs text-muted-foreground hover:text-foreground"
          data-testid="terms-btn"
        >
          <Shield className="h-3 w-3" />
          Terms of Use
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="font-['Chivo'] flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            Terms of Use & Limitation of Liability
          </DialogTitle>
          <DialogDescription>
            Please read these terms carefully before using Class-B HS Code Agent
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-6 text-sm mt-4">
          {/* Estimates Disclaimer */}
          <div className="space-y-2">
            <h3 className="font-semibold flex items-center gap-2 text-foreground">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              Estimates & Calculations
            </h3>
            <p className="text-muted-foreground leading-relaxed">
              All figures produced by our calculators are for <strong className="text-foreground">informational purposes only</strong>. 
              Class-B HS Code Agent does not warrant the completeness or accuracy of any calculation. 
              Actual duties may vary based on current rates, Customs Officer assessments, and regulatory changes.
            </p>
          </div>

          <Separator />

          {/* Classification Disclaimer */}
          <div className="space-y-2">
            <h3 className="font-semibold flex items-center gap-2 text-foreground">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              No Guarantee of Classification
            </h3>
            <p className="text-muted-foreground leading-relaxed">
              Correct tariff placement is the <strong className="text-foreground">sole responsibility of the user/broker</strong>. 
              We do not guarantee that the tariff codes suggested or used by this app will be accepted by regulatory authorities. 
              Users should verify all HS code classifications with official Bahamas Customs publications and officers.
            </p>
          </div>

          <Separator />

          {/* Non-Affiliation */}
          <div className="space-y-2">
            <h3 className="font-semibold flex items-center gap-2 text-foreground">
              <Shield className="h-4 w-4 text-blue-400" />
              Non-Affiliation & Unofficial Status
            </h3>
            <p className="text-muted-foreground leading-relaxed">
              This application is a <strong className="text-foreground">private support aid</strong> and is 
              <strong className="text-foreground"> not affiliated with or endorsed by</strong> the Bahamas Customs Department 
              or the Ministry of Finance. All official queries should be directed to Bahamas Customs directly.
            </p>
          </div>

          <Separator />

          {/* Reliance & Liability */}
          <div className="space-y-2">
            <h3 className="font-semibold flex items-center gap-2 text-foreground">
              <AlertTriangle className="h-4 w-4 text-rose-400" />
              Reliance & Limitation of Liability
            </h3>
            <p className="text-muted-foreground leading-relaxed">
              Users who rely on these estimates for commercial bidding, pricing, or logistics planning 
              <strong className="text-foreground"> do so at their own risk</strong>. The developers and operators 
              of Class-B HS Code Agent shall not be liable for any financial discrepancies, fines, delays, 
              or other damages resulting from the use of this data.
            </p>
          </div>

          <Separator />

          {/* User Responsibilities */}
          <div className="p-4 bg-primary/10 rounded-lg border border-primary/20 space-y-2">
            <h3 className="font-semibold text-primary">User Responsibilities</h3>
            <ul className="text-muted-foreground space-y-1 list-disc list-inside text-xs">
              <li>Verify all HS codes before submitting declarations</li>
              <li>Confirm current duty rates with official sources</li>
              <li>Maintain proper documentation for all imports</li>
              <li>Consult licensed customs brokers for complex classifications</li>
              <li>Report any errors or discrepancies found in the tool</li>
            </ul>
          </div>

          {/* Official Contact */}
          <div className="p-4 bg-muted/50 rounded-lg space-y-2">
            <h4 className="font-semibold text-sm">Official Resources</h4>
            <div className="flex flex-wrap gap-2 text-xs">
              <a 
                href="https://www.bahamas.gov.bs/customs" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2 py-1 bg-background rounded hover:bg-muted"
              >
                <ExternalLink className="h-3 w-3" />
                Bahamas Customs
              </a>
              <a 
                href="tel:+12423256550" 
                className="inline-flex items-center gap-1 px-2 py-1 bg-background rounded hover:bg-muted"
              >
                📞 +1 (242) 325-6550
              </a>
              <a 
                href="mailto:customs@bahamas.gov.bs" 
                className="inline-flex items-center gap-1 px-2 py-1 bg-background rounded hover:bg-muted"
              >
                ✉️ customs@bahamas.gov.bs
              </a>
            </div>
          </div>

          <p className="text-xs text-center text-muted-foreground/70 pt-2">
            By using Class-B HS Code Agent, you acknowledge and accept these terms.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
