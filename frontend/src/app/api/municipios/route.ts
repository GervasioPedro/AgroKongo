import { NextResponse } from 'next/server';

const MUNICIPIOS_POR_PROVINCIA: Record<string, string[]> = {
  "1": ["Luanda", "Belas", "Cacuaco", "Cazenga", "Icolo e Bengo", "Quiçama", "Viana"],
  "2": ["Ambriz", "Bula Atumba", "Dande", "Dembos", "Nambuangongo", "Pango Aluquém"],
  "3": ["Benguela", "Baía Farta", "Balombo", "Bocoio", "Caimbambo", "Catumbela", "Chongorói", "Cubal", "Ganda", "Lobito"],
  "4": ["Andulo", "Camacupa", "Catabola", "Chinguar", "Chitembo", "Cuemba", "Cunhinga", "Cuíto", "Nharea"],
  "5": ["Cabinda", "Belize", "Buco-Zau", "Cacongo"],
  "6": ["Calai", "Cuangar", "Cuchi", "Cuito Cuanavale", "Dirico", "Mavinga", "Menongue", "Nankova", "Rivungo"],
  "7": ["Ambaca", "Banga", "Bolongongo", "Cambambe", "Cazengo", "Golungo Alto", "Gonguembo", "Lucala", "Quiculungo", "Samba Caju"],
  "8": ["Amboim", "Cassongue", "Cela", "Conda", "Ebo", "Libolo", "Mussende", "Porto Amboim", "Quibala", "Quilenda", "Seles", "Sumbe"],
  "9": ["Cahama", "Cuanhama", "Curoca", "Cuvelai", "Namacunde", "Ombadja"],
  "10": ["Bailundo", "Catchiungo", "Caála", "Ecunha", "Huambo", "Londuimbali", "Longonjo", "Mungo", "Chicala-Choloanga", "Chinjenje", "Ucuma"],
  "11": ["Caconda", "Cacula", "Caluquembe", "Chiange", "Chibia", "Chicomba", "Chipindo", "Cuvango", "Humpata", "Jamba", "Lubango", "Matala", "Quilengues", "Quipungo"],
  "12": ["Cambulo", "Capenda-Camulemba", "Caungula", "Chitato", "Cuango", "Cuílo", "Lubalo", "Lucapa", "Xá-Muteba"],
  "13": ["Cacolo", "Dala", "Muconda", "Saurimo"],
  "14": ["Cacuso", "Calandula", "Cambundi-Catembo", "Cangandala", "Caombo", "Cuaba Nzogo", "Cunda-Dia-Baze", "Luquembo", "Malanje", "Marimba", "Massango", "Mucari", "Quela", "Quirima"],
  "15": ["Alto Zambeze", "Bundas", "Camanongue", "Cameia", "Léua", "Luau", "Luacano", "Luchazes", "Moxico"],
  "16": ["Bibala", "Camucuio", "Namibe", "Tômbwa", "Virei"],
  "17": ["Alto Cauale", "Ambuíla", "Bembe", "Buengas", "Bungo", "Damba", "Milunga", "Mucaba", "Negage", "Puri", "Quimbele", "Quitexe", "Sanza Pombo", "Songo", "Uíge", "Zombo"],
  "18": ["Cuimba", "Mbanza Kongo", "Nóqui", "Nzeto", "Soyo", "Tomboco"],
};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const provinciaId = searchParams.get('provincia_id');

  if (!provinciaId) {
    return NextResponse.json({ error: 'provincia_id é obrigatório' }, { status: 400 });
  }

  const municipios = MUNICIPIOS_POR_PROVINCIA[provinciaId] || [];

  return NextResponse.json({
    provincia_id: provinciaId,
    municipios: municipios
  });
}
