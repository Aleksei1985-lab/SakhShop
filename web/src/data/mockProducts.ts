interface Product {
    id: number;
    title: string;
    description: string;
    price: number;
    image: string;
  }
  
  export const products: Product[] = [
    {
      id: 1,
      title: 'Сахалинский краб',
      description: 'Свежий камчатский краб, выловленный в Охотском море',
      price: 2500,
      image: '/images/crab.jpg'
    },
    {
      id: 2,
      title: 'Морской ёж',
      description: 'Свежие морские ежи с побережья Сахалина',
      price: 500,
      image: '/images/urchin.jpg'
    },
    {
      id: 3,
      title: 'Икра горбуши',
      description: 'Натуральная икра горбуши, 100г',
      price: 1200,
      image: '/images/caviar.jpg'
    },
    {
      id: 4,
      title: 'Морская капуста',
      description: 'Сушёная морская капуста, 200г',
      price: 300,
      image: '/images/seaweed.jpg'
    }
  ];