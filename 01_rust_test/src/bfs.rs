use std::collections::{VecDeque, HashSet};
use image::{ImageBuffer, RgbImage, Rgb, ImageReader, Limits};

use rand::{Rng, SeedableRng};
use rand::rngs::StdRng;

pub type Point = (usize, usize);


/// 8방향 이웃 중 skeleton[y][x] == 1인 좌표를 반환
fn get_neighbors(point: Point, skeleton: &Vec<Vec<u8>>) -> Vec<Point> {
    let (x, y) = point;
    let mut neighbors = Vec::new();
    let dirs = [-1, 0, 1];
    let height = skeleton.len() as i32;
    let width = skeleton[0].len() as i32;
    let xi = x as i32;
    let yi = y as i32;
    for dx in dirs {
        for dy in dirs {
            if dx == 0 && dy == 0 { continue; }
            let nx = xi + dx;
            let ny = yi + dy;
            if nx >= 0 && nx < width && ny >= 0 && ny < height {
                let ux = nx as usize;
                let uy = ny as usize;
                if skeleton[uy][ux] == 1 {
                    neighbors.push((ux, uy));
                }
            }
        }
    }
    neighbors
}

/// 분기점 여부: 이웃이 3개 이상
fn is_branch_point(point: Point, skeleton: &Vec<Vec<u8>>) -> bool {
    get_neighbors(point, skeleton).len() >= 3
}

/// 끝점 여부: 이웃이 1개
fn is_end_point(point: Point, skeleton: &Vec<Vec<u8>>) -> bool {
    get_neighbors(point, skeleton).len() == 1
}

/// 끝점들 중 y좌표-우선, x좌표-두번째 기준으로 가장 왼쪽/위의 점 선택
fn select_topleft_start_point(end_points: &[Point]) -> Option<Point> {
    if end_points.is_empty() { return None; }
    let mut min_point = end_points[0];
    for &p in end_points.iter().skip(1) {
        if p.1 < min_point.1 || (p.1 == min_point.1 && p.0 < min_point.0) {
            min_point = p;
        }
    }
    Some(min_point)
}

//스켈레톤 가져오기

pub fn load_skeleton_from_png(path: &str, threshold: u8) -> image::ImageResult<Vec<Vec<u8>>> {
    let mut reader = ImageReader::open(path)?;

    let mut limits = Limits::default();
    limits.max_alloc = Some(2 * 1024 * 1024 * 1024); // 2GiB
    reader.limits(limits);

    let img = reader.decode()?.to_luma8();
    // 이하 동일...
     let (w, h) = img.dimensions();
     let mut s = Vec::with_capacity(h as usize);
     for y in 0..h {
         let mut row = Vec::with_capacity(w as usize);
         for x in 0..w {
             let v = img.get_pixel(x, y)[0];
             row.push(if v >= threshold { 1 } else { 0 });
         }
         s.push(row);
     }
     Ok(s)
}




/// BFS로 모든 경로 추출 후 길이 10 이하의 경로는 제거
pub fn extract_all_paths_with_end_points(
    skeleton: &Vec<Vec<u8>>,
    end_points: Vec<Point>,
) -> Vec<Vec<Point>> {
    let start = match select_topleft_start_point(&end_points) {
        Some(p) => p,
        None => return Vec::new(),
    };
    // 시작점이 0인 경우 빈 결과
    if skeleton[start.1][start.0] == 0 {
        return Vec::new();
    }

    let mut all_paths: Vec<Vec<Point>> = Vec::new();
    let mut visited: HashSet<Point> = HashSet::new();
    let mut queue: VecDeque<(Point, Vec<Point>)> = VecDeque::new();
    queue.push_back((start, vec![start]));

    while let Some((current, path)) = queue.pop_front() {
        if visited.contains(&current) {
            continue;
        }
        visited.insert(current);

        let endpoint = is_end_point(current, skeleton);
        let branch = is_branch_point(current, skeleton);
        // 시작점이 아닌 끝점 또는 분기점이면 현재 경로 저장
        if current != start && (endpoint || branch) {
            all_paths.push(path.clone());
            
            // ✅ 여기서 몇 번째 균열인지 출력
            println!(
                "[BFS] {}번째 균열 경로 발견 (길이: {}, 끝점: {:?})",
                all_paths.len(),   // 1번째, 2번째, ...
                path.len(),
                current
            );

            if branch {
                // 분기점이면 현재 좌표에서 다시 BFS 시작
                for neighbor in get_neighbors(current, skeleton) {
                    if !visited.contains(&neighbor) {
                        queue.push_back((neighbor, vec![current, neighbor]));
                    }
                }
                continue; // 각 분기는 새 큐에서 처리
            }
        }
        // 그 외에는 이웃으로 경로 확장
        for neighbor in get_neighbors(current, skeleton) {
            if !visited.contains(&neighbor) {
                let mut new_path = path.clone();
                new_path.push(neighbor);
                queue.push_back((neighbor, new_path));
            }
        }
    }

    // 길이 10 이하 경로 제거
    all_paths.into_iter().filter(|p| p.len() > 10).collect()
}

// ========================================================================= 
// 시각화 코드 

pub fn visualize_paths(
    paths: &Vec<Vec<Point>>,
    width: u32,
    height: u32,
    out_path: &str,
) -> image::ImageResult<()> {
    // 배경 검정
    let mut img: RgbImage = ImageBuffer::from_pixel(width, height, Rgb([0, 0, 0]));

    // 재현 가능한 랜덤 색
    let mut rng = StdRng::seed_from_u64(1234);

    for path in paths {
        let color = Rgb([
            rng.gen_range(80..255),
            rng.gen_range(80..255),
            rng.gen_range(80..255),
        ]);

        for &(x, y) in path {
            // 범위 체크
            if x < width as usize && y < height as usize {
                img.put_pixel(x as u32, y as u32, color);
            }
        }
    }

    img.save(out_path)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn simple_line_path() {
        let skeleton = vec![vec![1u8; 15]];
        let end_points = vec![(0usize, 0usize), (14usize, 0usize)];

        let paths = extract_all_paths_with_end_points(&skeleton, end_points);

        let height = skeleton.len() as u32;
        let width = skeleton[0].len() as u32;

        // cracks.png 라는 파일에 저장
        visualize_paths(&paths, width, height, "cracks.png").unwrap();

        assert_eq!(paths.len(), 1);
        assert!(paths[0].len() > 10);
        assert_eq!(paths[0].first().copied(), Some((0, 0)));
        assert_eq!(paths[0].last().copied(), Some((14, 0)));
    }
}

// #[cfg(test)]
// mod tests {
//     use super::*;

//     #[test]
//     fn simple_line_path() {
//         let skeleton = vec![vec![1u8; 15]];
//         let end_points = vec![(0usize, 0usize), (14usize, 0usize)];

//         let paths = extract_all_paths_with_end_points(&skeleton, end_points);

//         assert_eq!(paths.len(), 1);
//         assert!(paths[0].len() > 10);
//         assert_eq!(paths[0].first().copied(), Some((0, 0)));
//         assert_eq!(paths[0].last().copied(), Some((14, 0)));
//     }
// }