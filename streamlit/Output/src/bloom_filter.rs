pub struct BloomFilter<T> {
    pub hash_func: fn(T) -> u32,
    pub table: Vec<u8>,
    pub table_size: u32,
    pub num_functions: u32,
}

pub const SALTS: [u32; 64] = [
    0x1953c322, 0x588ccf17, 0x64bf600c, 0xa6be3f3d, 0x341a02ea, 0x15b03217, 0x3b062858, 0x5956fd06,
    0x18b5624f, 0xe3be0b46, 0x20ffcd5c, 0xa35dfd2b, 0x1fc4a9bf, 0x57c45d5c, 0xa8661c4a, 0x4f1b74d2,
    0x5a6dde13, 0x3b18dac6, 0x05a8afbf, 0xbbda2fe2, 0xa2520d78, 0xe7934849, 0xd541bc75, 0x09a55b57,
    0x9b345ae2, 0xfc2d26af, 0x38679cef, 0x81bd1e0d, 0x654681ae, 0x4b3d87ad, 0xd5ff10fb, 0x23b32f67,
    0xafc7e366, 0xdd955ead, 0xe7c34b1c, 0xfeace0a6, 0xeb16f09d, 0x3c57a72d, 0x2c8294c5, 0xba92662a,
    0xcd5b2d14, 0x743936c8, 0x2489beff, 0xc6c56e00, 0x74a4f606, 0xb244a94a, 0x5edfc423, 0xf1901934,
    0x24af7691, 0xf6c98b25, 0xea25af46, 0x76d5f2e6, 0x5e33cdf2, 0x445eb357, 0x88556bd2, 0x70d1da7a,
    0x54449368, 0x381020bc, 0x1c0520bf, 0xf7e44942, 0xa27e2a58, 0x66866fc5, 0x12519ce7, 0x437a8456,
];
pub fn bloom_filter_new<T>(
    table_size: u32,
    hash_func: fn(T) -> u32,
    num_functions: u32,
) -> Option<BloomFilter<T>> {
    if num_functions > SALTS.len() as u32 {
        return None;
    }

    let table = vec![0u8; ((table_size + 7) / 8) as usize];

    Some(BloomFilter {
        hash_func,
        table,
        table_size,
        num_functions,
    })
}

pub fn bloom_filter_query<T: Clone>(bloomfilter: &BloomFilter<T>, value: T) -> i32 {
    let hash = (bloomfilter.hash_func)(value.clone());
    let mut subhash: u32;
    let mut index: usize;
    let mut b: u8;
    let mut bit: u8;

    for _i in 0..bloomfilter.num_functions {
        subhash = hash ^ SALTS[_i as usize];
        index = (subhash % bloomfilter.table_size) as usize;
        b = bloomfilter.table[index / 8];
        bit = 1 << (index % 8);

        if (b & bit) == 0 {
            return 0;
        }
    }

    1
}

pub fn bloom_filter_insert<T: Clone>(bloomfilter: &mut BloomFilter<T>, value: T) {
    let hash = (bloomfilter.hash_func)(value.clone());
    let mut subhash;
    let mut index;
    let mut i: u32 = 0;
    let mut b: u8;

    while i < bloomfilter.num_functions {
        subhash = hash ^ SALTS[i as usize];
        index = subhash % bloomfilter.table_size;
        b = 1 << (index % 8);
        bloomfilter.table[(index / 8) as usize] |= b;
        i += 1;
    }
}

pub fn bloom_filter_free<T>(bloomfilter: &mut BloomFilter<T>) {
    bloomfilter.table.clear();
}

pub fn bloom_filter_read<T>(bloomfilter: &BloomFilter<T>, array: &mut [u8]) {
    let mut array_size = (bloomfilter.table_size + 7) / 8;
    array[..array_size as usize].copy_from_slice(&bloomfilter.table[..array_size as usize]);
}

pub fn bloom_filter_load<T>(bloomfilter: &mut BloomFilter<T>, array: &[u8]) {
    let mut array_size = (bloomfilter.table_size + 7) / 8;
    bloomfilter.table[..array_size as usize].copy_from_slice(&array[..array_size as usize]);
}

pub fn bloom_filter_union<T>(
    filter1: &BloomFilter<T>,
    filter2: &BloomFilter<T>,
) -> Option<BloomFilter<T>> {
    if filter1.table_size != filter2.table_size
        || filter1.num_functions != filter2.num_functions
        || filter1.hash_func as *const () != filter2.hash_func as *const ()
    {
        return None;
    }

    let mut result =
        bloom_filter_new(filter1.table_size, filter1.hash_func, filter1.num_functions)?;

    let array_size = (filter1.table_size + 7) / 8;

    for i in 0..array_size {
        result.table[i as usize] = filter1.table[i as usize] | filter2.table[i as usize];
    }

    Some(result)
}

pub fn bloom_filter_intersection<T>(
    filter1: &BloomFilter<T>,
    filter2: &BloomFilter<T>,
) -> Option<BloomFilter<T>> {
    if filter1.table_size != filter2.table_size
        || filter1.num_functions != filter2.num_functions
        || filter1.hash_func as *const () != filter2.hash_func as *const ()
    {
        return None;
    }

    let mut result =
        bloom_filter_new(filter1.table_size, filter1.hash_func, filter1.num_functions)?;

    let array_size = (filter1.table_size + 7) / 8;

    for i in 0..array_size {
        result.table[i as usize] = filter1.table[i as usize] & filter2.table[i as usize];
    }

    Some(result)
}
