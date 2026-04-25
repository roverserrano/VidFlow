const expected = process.argv[2];

if (!expected) {
  console.error("Uso: node scripts/assert-platform.js <platform>");
  process.exit(1);
}

if (process.platform !== expected) {
  console.error(
    `Este build debe ejecutarse en '${expected}', pero detecte '${process.platform}'.`
  );
  console.error(
    "Para evitar instaladores rotos, genera los binarios de Windows en Windows y los de Linux en Linux."
  );
  process.exit(1);
}

