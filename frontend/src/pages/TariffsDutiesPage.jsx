import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { ScrollArea } from '../components/ui/scroll-area';
import { Separator } from '../components/ui/separator';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '../components/ui/accordion';
import { 
  Search, 
  DollarSign,
  Percent,
  Scale,
  BookOpen,
  FileText,
  AlertTriangle,
  Info,
  ChevronRight,
  Calculator,
  Package,
  Wine,
  Cigarette,
  Shield,
  Globe,
  HelpCircle
} from 'lucide-react';
import { cn } from '../lib/utils';

// Bahamas Tariff Sections
const TARIFF_SECTIONS = [
  { section: 'I', chapters: '1-5', title: 'Live Animals; Animal Products', icon: '🐄' },
  { section: 'II', chapters: '6-14', title: 'Vegetable Products', icon: '🌿' },
  { section: 'III', chapters: '15', title: 'Animal or Vegetable Fats and Oils', icon: '🫒' },
  { section: 'IV', chapters: '16-24', title: 'Prepared Foodstuffs; Beverages, Spirits, Tobacco', icon: '🍷' },
  { section: 'V', chapters: '25-27', title: 'Mineral Products', icon: '⛏️' },
  { section: 'VI', chapters: '28-38', title: 'Products of the Chemical or Allied Industries', icon: '🧪' },
  { section: 'VII', chapters: '39-40', title: 'Plastics and Rubber', icon: '🔧' },
  { section: 'VIII', chapters: '41-43', title: 'Leather, Furskins, Saddlery', icon: '👜' },
  { section: 'IX', chapters: '44-46', title: 'Wood and Articles of Wood', icon: '🪵' },
  { section: 'X', chapters: '47-49', title: 'Pulp of Wood; Paper and Paperboard', icon: '📄' },
  { section: 'XI', chapters: '50-63', title: 'Textiles and Textile Articles', icon: '🧵' },
  { section: 'XII', chapters: '64-67', title: 'Footwear, Headgear, Umbrellas', icon: '👟' },
  { section: 'XIII', chapters: '68-70', title: 'Stone, Plaster, Cement; Ceramics; Glass', icon: '🪨' },
  { section: 'XIV', chapters: '71', title: 'Pearls, Precious Stones, Precious Metals', icon: '💎' },
  { section: 'XV', chapters: '72-83', title: 'Base Metals and Articles', icon: '🔩' },
  { section: 'XVI', chapters: '84-85', title: 'Machinery and Electrical Equipment', icon: '⚙️' },
  { section: 'XVII', chapters: '86-89', title: 'Vehicles, Aircraft, Vessels', icon: '✈️' },
  { section: 'XVIII', chapters: '90-92', title: 'Optical, Medical, Musical Instruments', icon: '🔬' },
  { section: 'XIX', chapters: '93', title: 'Arms and Ammunition', icon: '🎯' },
  { section: 'XX', chapters: '94-96', title: 'Miscellaneous Manufactured Articles', icon: '🪑' },
  { section: 'XXI', chapters: '97', title: 'Works of Art, Collectors Pieces, Antiques', icon: '🖼️' },
  { section: 'Special', chapters: '98-99', title: 'Special Classifications & Exemptions', icon: '📋' },
];

// Common Duty Rates
const COMMON_DUTY_RATES = [
  { category: 'Refrigerators & Appliances', rate: '5%', notes: 'Energy-efficient appliances' },
  { category: 'All Types of Waters', rate: '100%', notes: 'Protection for local water industry' },
  { category: 'Unmanufactured Tobacco', rate: '10%', notes: 'Raw tobacco leaves' },
  { category: 'Manufactured Tobacco', rate: '220%', notes: 'Cigarettes, cigars, etc.' },
  { category: 'Basic Foodstuffs', rate: '0-10%', notes: 'Essential food items' },
  { category: 'Clothing & Textiles', rate: '25-35%', notes: 'Apparel and fabrics' },
  { category: 'Electronics', rate: '5-15%', notes: 'Computers, phones, etc.' },
  { category: 'Motor Vehicles', rate: '25-85%', notes: 'Varies by type and value' },
  { category: 'Wine & Beer', rate: '35-45%', notes: 'Plus excise duty' },
  { category: 'Spirits', rate: '35-45%', notes: 'Plus excise duty' },
  { category: 'Building Materials', rate: '0-35%', notes: 'Varies by material' },
  { category: 'Medical Equipment', rate: '0%', notes: 'Exempt when for public use' },
];

// Excise Duty Information
const EXCISE_DUTIES = [
  { 
    category: 'Alcoholic Beverages',
    items: [
      { item: 'Beer (per liter of pure alcohol)', rate: '$5.00/LPA', notes: 'Spirits and Beer Manufacture Act' },
      { item: 'Wine (still)', rate: '$2.50/liter', notes: 'Chapters 22' },
      { item: 'Wine (sparkling)', rate: '$4.00/liter', notes: 'Champagne, etc.' },
      { item: 'Spirits (rum, vodka, whiskey)', rate: '$8.00/LPA', notes: 'Chapters 22' },
      { item: 'Liqueurs and cordials', rate: '$6.00/LPA', notes: 'Sweetened spirits' },
    ]
  },
  {
    category: 'Tobacco Products',
    items: [
      { item: 'Cigarettes', rate: '$0.25/stick', notes: 'Per individual cigarette' },
      { item: 'Cigars', rate: '$1.50/each', notes: 'Per cigar' },
      { item: 'Smoking tobacco', rate: '$15.00/kg', notes: 'Loose tobacco' },
      { item: 'Chewing tobacco', rate: '$10.00/kg', notes: 'Smokeless tobacco' },
    ]
  },
  {
    category: 'Petroleum Products',
    items: [
      { item: 'Motor gasoline', rate: '$0.75/gallon', notes: 'Fuel tax' },
      { item: 'Diesel', rate: '$0.60/gallon', notes: 'Fuel tax' },
      { item: 'Kerosene', rate: '$0.40/gallon', notes: 'Heating and lighting' },
      { item: 'Lubricating oils', rate: '5%', notes: 'Ad valorem' },
    ]
  },
];

// General Rules of Interpretation
const GRI_RULES = [
  {
    rule: 'GRI 1',
    title: 'Headings and Section/Chapter Notes',
    description: 'Classification shall be determined according to the terms of the headings and any relative Section or Chapter Notes. This is the first and most common rule applied.',
    example: 'If a product is clearly described by the text of a heading (e.g., "Live animals" under Chapter 1), it is classified under that heading.',
    key: 'Always start here - read the heading descriptions first'
  },
  {
    rule: 'GRI 2(a)',
    title: 'Incomplete or Unassembled Goods',
    description: 'Incomplete or unfinished articles that have the essential character of the complete article are classified as the complete item. Also applies to disassembled goods.',
    example: 'An automobile missing wheels would still be classified as a complete automobile. Unassembled furniture kit is classified as furniture.',
    key: 'Essential character determines classification'
  },
  {
    rule: 'GRI 2(b)',
    title: 'Mixtures and Combinations',
    description: 'A heading referring to a material includes mixtures of that substance with others. Goods made partly of a material are included.',
    example: 'Paint containing pigments, binders, and solvents is classified as paint. A wooden table with metal legs is classified as a table.',
    key: 'Mixed materials follow the primary material'
  },
  {
    rule: 'GRI 3(a)',
    title: 'Most Specific Description',
    description: 'When goods could be classified under multiple headings, prefer the heading with the most specific description.',
    example: 'Electric shavers would be classified under "Shavers and hair clippers" (85.10) rather than general "Electro-mechanical domestic appliances" (85.09).',
    key: 'Specific beats general'
  },
  {
    rule: 'GRI 3(b)',
    title: 'Essential Character',
    description: 'For mixtures, composites, and retail sets that cannot be classified by 3(a), classify by the component that gives essential character.',
    example: 'A spaghetti dinner set\'s essential character is the uncooked spaghetti. A leather briefcase with metal frame is classified as leather goods.',
    key: 'What gives the product its identity?'
  },
  {
    rule: 'GRI 3(c)',
    title: 'Last Heading in Numerical Order',
    description: 'When 3(a) and 3(b) cannot resolve classification, use the heading that appears last numerically.',
    example: 'A set of comb, brush, and mirror (none dominant) would be classified under heading 96.15 as it appears last.',
    key: 'Tiebreaker - higher number wins'
  },
  {
    rule: 'GRI 4',
    title: 'Most Akin (Similar Goods)',
    description: 'Goods that cannot be classified by Rules 1-3 are classified under the heading for goods to which they are most similar.',
    example: 'A novel type of household cleaning tool might be classified with existing cleaning tools it resembles most.',
    key: 'Classification by analogy'
  },
  {
    rule: 'GRI 5(a)',
    title: 'Cases and Containers',
    description: 'Specially shaped containers (camera cases, gun cases, instrument cases) presented with articles are classified with those articles.',
    example: 'A violin case presented with the violin is classified together. A guitar case sold with the guitar.',
    key: 'Container follows the product'
  },
  {
    rule: 'GRI 5(b)',
    title: 'Packing Materials',
    description: 'Normal packing materials presented with goods are classified with the goods, unless clearly suitable for repetitive use.',
    example: 'A cardboard box containing wine glasses is classified with the glasses. Reusable shipping crates are classified separately.',
    key: 'Normal packing = part of product'
  },
  {
    rule: 'GRI 6',
    title: 'Subheading Classification',
    description: 'For subheading classification, apply the same rules (1-5) at the subheading level. Only compare subheadings at the same level.',
    example: 'Once classified under Heading 8517 (Telephone sets), use GRI 1-5 to determine if "wired" or "wireless" subheading applies.',
    key: 'Same rules apply at every level'
  },
];

// Duty Exemptions (Chapter 98)
const DUTY_EXEMPTIONS = [
  { category: 'Agricultural', items: ['Agricultural equipment', 'Horticultural goods', 'Fisheries equipment', 'Forestry supplies'], notes: 'For agricultural development' },
  { category: 'Personal', items: ['Returning resident baggage', 'Used personal clothing', 'Household effects of public officers'], notes: 'Subject to conditions' },
  { category: 'Educational', items: ['Educational materials', 'Scientific equipment', 'Cultural goods', 'School supplies'], notes: 'For accredited institutions' },
  { category: 'Medical', items: ['Medical equipment for public facilities', 'Pharmaceutical products', 'Hospital supplies'], notes: 'Public health facilities' },
  { category: 'Religious', items: ['Religious artifacts', 'Church furnishings', 'Religious publications'], notes: 'For recognized organizations' },
  { category: 'Sporting', items: ['Sporting equipment', 'Athletic gear', 'Tournament trophies'], notes: 'For registered organizations' },
  { category: 'Tourism', items: ['Promotional materials', 'Bahamian cultural reproductions'], notes: 'Tourism promotion' },
  { category: 'Industry', items: ['Cottage industry materials', 'Printing equipment', 'Manufacturing samples'], notes: 'Local industry support' },
  { category: 'Relief', items: ['Relief goods', 'Disaster supplies', 'Charitable donations'], notes: 'Emergency response' },
  { category: 'Maritime', items: ['Marine vessels (specified)', 'Inter-island service vessels', 'Vessel parts'], notes: 'Maritime operations' },
  { category: 'Housing', items: ['Systems building materials', 'Government housing project materials'], notes: 'Public housing' },
  { category: 'Art & Culture', items: ['Works of art', 'Collectors pieces', 'Antiques'], notes: 'Cultural preservation' },
];

export default function TariffsDutiesPage() {
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('overview');

  const filteredRates = COMMON_DUTY_RATES.filter(rate =>
    rate.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    rate.notes.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredGRI = GRI_RULES.filter(rule =>
    rule.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    rule.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    rule.example.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredSections = TARIFF_SECTIONS.filter(section =>
    section.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.section.toLowerCase().includes(searchQuery.toLowerCase()) ||
    section.chapters.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredExcise = EXCISE_DUTIES.map(category => ({
    ...category,
    items: category.items.filter(item =>
      item.item.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.notes.toLowerCase().includes(searchQuery.toLowerCase()) ||
      category.category.toLowerCase().includes(searchQuery.toLowerCase())
    )
  })).filter(category => category.items.length > 0);

  const filteredExemptions = DUTY_EXEMPTIONS.filter(exemption =>
    exemption.notes.toLowerCase().includes(searchQuery.toLowerCase()) ||
    exemption.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    exemption.items.some(item => item.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="space-y-6" data-testid="tariffs-duties-page">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold font-['Chivo'] tracking-tight">
            Tariffs & Excise Duties
          </h1>
          <p className="text-muted-foreground mt-1">
            Bahamas Customs duty rates, excise taxes, and classification rules
          </p>
        </div>
        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search rates, rules, exemptions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
            data-testid="tariff-search"
          />
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-5 w-full max-w-2xl">
          <TabsTrigger value="overview" data-testid="tab-overview">
            <Scale className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="sections" data-testid="tab-sections">
            <Package className="h-4 w-4 mr-2" />
            Sections
          </TabsTrigger>
          <TabsTrigger value="excise" data-testid="tab-excise">
            <Wine className="h-4 w-4 mr-2" />
            Excise
          </TabsTrigger>
          <TabsTrigger value="gri" data-testid="tab-gri">
            <BookOpen className="h-4 w-4 mr-2" />
            GRI Rules
          </TabsTrigger>
          <TabsTrigger value="exemptions" data-testid="tab-exemptions">
            <Shield className="h-4 w-4 mr-2" />
            Exemptions
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6 mt-6">
          {/* Key Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="bg-gradient-to-br from-primary/10 to-primary/5 border-primary/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Percent className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">0% - 220%</p>
                    <p className="text-sm text-muted-foreground">Duty Rate Range</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-amber-500/10 to-amber-500/5 border-amber-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-amber-500/20 rounded-lg">
                    <DollarSign className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">10%</p>
                    <p className="text-sm text-muted-foreground">VAT Rate</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-gradient-to-br from-emerald-500/10 to-emerald-500/5 border-emerald-500/20">
              <CardContent className="pt-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-emerald-500/20 rounded-lg">
                    <Globe className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">EPA</p>
                    <p className="text-sm text-muted-foreground">Preferential Rates</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Tariff Structure */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Info className="h-5 w-5 text-primary" />
                Bahamas Tariff Structure
              </CardTitle>
              <CardDescription>
                The Bahamas uses the Harmonized System (HS) with an 8-digit code
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-muted/30 rounded-lg">
                  <h4 className="font-semibold mb-2">Code Structure</h4>
                  <div className="font-mono text-lg space-y-1">
                    <p><span className="text-primary">XX</span>.XX.XX.<span className="text-amber-500">XX</span></p>
                    <p className="text-xs text-muted-foreground">
                      <span className="text-primary">Chapter</span> • Heading • Subheading • <span className="text-amber-500">Bahamas Specific</span>
                    </p>
                  </div>
                </div>
                <div className="p-4 bg-muted/30 rounded-lg">
                  <h4 className="font-semibold mb-2">Tariff Schedule Parts</h4>
                  <ul className="text-sm space-y-1">
                    <li><Badge variant="outline" className="mr-2">Part A</Badge>General Rules of Interpretation</li>
                    <li><Badge variant="outline" className="mr-2">Part B</Badge>Additional Rules</li>
                    <li><Badge variant="outline" className="mr-2">Part C</Badge>HS Nomenclature & Rates</li>
                    <li><Badge variant="outline" className="mr-2">Part D</Badge>Chapter 98 (Exemptions)</li>
                  </ul>
                </div>
              </div>

              <Separator />

              <div>
                <h4 className="font-semibold mb-3">Rate Columns in Tariff Schedule</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <div className="p-3 border rounded-lg">
                    <p className="font-medium text-sm">Column 3: General Rate</p>
                    <p className="text-xs text-muted-foreground">Standard duty rate for all imports</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="font-medium text-sm">Column 4: Specific Rate</p>
                    <p className="text-xs text-muted-foreground">Per unit (kg, liter, etc.)</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="font-medium text-sm">Column 5: Max Variable Rate</p>
                    <p className="text-xs text-muted-foreground">Minister may impose by Order</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="font-medium text-sm">Column 6: EPA Preferential</p>
                    <p className="text-xs text-muted-foreground">CARIFORUM/EU rates</p>
                  </div>
                  <div className="p-3 border rounded-lg">
                    <p className="font-medium text-sm">Column 7: Statistical</p>
                    <p className="text-xs text-muted-foreground">Unit of measure codes</p>
                  </div>
                  <div className="p-3 border rounded-lg bg-amber-500/10">
                    <p className="font-medium text-sm">** Symbol</p>
                    <p className="text-xs text-muted-foreground">Check Excise Schedule</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Common Duty Rates */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calculator className="h-5 w-5 text-primary" />
                Common Duty Rates
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {filteredRates.map((item, idx) => (
                  <div key={idx} className="p-3 border rounded-lg hover:bg-muted/30 transition-colors">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-sm">{item.category}</p>
                      <Badge variant="outline" className="font-mono">{item.rate}</Badge>
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">{item.notes}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Additional Duties */}
          <Card className="border-amber-500/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                Additional Duties & Charges
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-amber-500/10 rounded-lg">
                <p className="font-medium">Warehousing Duty: 1% ad valorem</p>
                <p className="text-sm text-muted-foreground">Applied to all goods entered for warehousing or re-warehousing</p>
              </div>
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="font-medium">VAT: 10%</p>
                <p className="text-sm text-muted-foreground">Applied to CIF value plus all duties</p>
              </div>
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="font-medium">Environmental Levy</p>
                <p className="text-sm text-muted-foreground">May apply to certain items (vehicles, appliances)</p>
              </div>
              <div className="p-3 bg-rose-500/10 rounded-lg">
                <p className="font-medium">Anti-dumping / Countervailing Duty</p>
                <p className="text-sm text-muted-foreground">May be imposed by Minister on specific goods</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sections Tab */}
        <TabsContent value="sections" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Harmonized System Sections</CardTitle>
              <CardDescription>
                The HS is organized into 21 Sections plus special chapters (98-99)
              </CardDescription>
            </CardHeader>
            <CardContent>
              {filteredSections.length === 0 && searchQuery ? (
                <p className="text-center text-muted-foreground py-8">No sections match "{searchQuery}"</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {filteredSections.map((section) => (
                    <div 
                      key={section.section} 
                      className="p-4 border rounded-lg hover:bg-muted/30 transition-colors cursor-pointer"
                      data-testid={`section-${section.section}`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{section.icon}</span>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="font-mono">
                              Section {section.section}
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              Ch. {section.chapters}
                            </span>
                          </div>
                          <p className="font-medium mt-1">{section.title}</p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Excise Tab */}
        <TabsContent value="excise" className="mt-6 space-y-6">
          <Card className="border-amber-500/30">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Wine className="h-5 w-5 text-amber-500" />
                <CardTitle>Excise Duty Schedule</CardTitle>
              </div>
              <CardDescription>
                Excise duties are levied in addition to import duties. The &quot;**&quot; symbol in the tariff indicates excise applies.
              </CardDescription>
            </CardHeader>
          </Card>

          {filteredExcise.length === 0 && searchQuery ? (
            <Card>
              <CardContent className="py-8 text-center text-muted-foreground">
                No excise duties match "{searchQuery}"
              </CardContent>
            </Card>
          ) : (
            filteredExcise.map((category, idx) => (
              <Card key={idx}>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    {category.category === 'Alcoholic Beverages' && <Wine className="h-5 w-5" />}
                    {category.category === 'Tobacco Products' && <Cigarette className="h-5 w-5" />}
                    {category.category === 'Petroleum Products' && <Package className="h-5 w-5" />}
                    {category.category}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {category.items.map((item, itemIdx) => (
                      <div key={itemIdx} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                        <div>
                          <p className="font-medium">{item.item}</p>
                          <p className="text-xs text-muted-foreground">{item.notes}</p>
                        </div>
                      <Badge className="font-mono bg-amber-500/20 text-amber-400 border-amber-500/30">
                        {item.rate}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))
          )}

          <Card className="bg-muted/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-primary mt-0.5" />
                <div>
                  <p className="font-medium">Excise Act Schedules</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    <strong>First Schedule:</strong> Excise tax rates for 381 items from Chapters 22-93<br />
                    <strong>Second Schedule:</strong> Chapter 98 exemptions for excisable goods
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* GRI Rules Tab */}
        <TabsContent value="gri" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5 text-primary" />
                General Rules of Interpretation (GRI)
              </CardTitle>
              <CardDescription>
                Six rules applied consecutively to classify goods. Always start with GRI 1.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {(searchQuery ? filteredGRI : GRI_RULES).map((rule, idx) => (
                  <AccordionItem key={idx} value={rule.rule} data-testid={`gri-${rule.rule}`}>
                    <AccordionTrigger className="hover:no-underline">
                      <div className="flex items-center gap-3 text-left">
                        <Badge variant="outline" className="font-mono shrink-0">
                          {rule.rule}
                        </Badge>
                        <span className="font-medium">{rule.title}</span>
                      </div>
                    </AccordionTrigger>
                    <AccordionContent className="space-y-4">
                      <p className="text-muted-foreground">{rule.description}</p>
                      
                      <div className="p-3 bg-primary/5 rounded-lg border-l-2 border-primary">
                        <p className="text-sm font-medium text-primary">Example:</p>
                        <p className="text-sm mt-1">{rule.example}</p>
                      </div>
                      
                      <div className="p-3 bg-amber-500/10 rounded-lg">
                        <p className="text-sm font-medium text-amber-400">Key Point:</p>
                        <p className="text-sm mt-1">{rule.key}</p>
                      </div>
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Exemptions Tab */}
        <TabsContent value="exemptions" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-emerald-500" />
                Chapter 98: Duty Exemptions & Concessions
              </CardTitle>
              <CardDescription>
                Special provisions for duty-free or reduced duty imports. Form C-63 required for most exemptions.
              </CardDescription>
            </CardHeader>
            <CardContent>
              {filteredExemptions.length === 0 && searchQuery ? (
                <p className="text-center text-muted-foreground py-8">No exemptions match "{searchQuery}"</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {filteredExemptions.map((exemption, idx) => (
                    <div key={idx} className="p-4 border rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                          {exemption.category}
                        </Badge>
                      </div>
                      <ul className="text-sm space-y-1 mb-2">
                        {exemption.items.map((item, itemIdx) => (
                          <li key={itemIdx} className="flex items-center gap-2">
                            <ChevronRight className="h-3 w-3 text-muted-foreground" />
                            {item}
                          </li>
                        ))}
                      </ul>
                      <p className="text-xs text-muted-foreground">{exemption.notes}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Important Notes */}
          <Card className="mt-6 border-primary/30">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HelpCircle className="h-5 w-5 text-primary" />
                Important Notes on Exemptions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="font-medium">Pre-Approval Required</p>
                <p className="text-sm text-muted-foreground">Most exemptions require prior approval before importation. Apply using Form C-63.</p>
              </div>
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="font-medium">Documentation</p>
                <p className="text-sm text-muted-foreground">Maintain records of exempt imports for 5+ years. Subject to audit.</p>
              </div>
              <div className="p-3 bg-amber-500/10 rounded-lg">
                <p className="font-medium">Hawksbill Creek Agreement</p>
                <p className="text-sm text-muted-foreground">Special duty rate for Freeport/Grand Bahama: 25% ad valorem of 40% of construction cost.</p>
              </div>
              <div className="p-3 bg-muted/30 rounded-lg">
                <p className="font-medium">EPA Preferential Rates</p>
                <p className="text-sm text-muted-foreground">Reduced rates for goods from EU and CARIFORUM countries. Check Column 6 of tariff schedule.</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
