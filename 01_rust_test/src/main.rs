mod bfs;

//bfs 파일에 두가지 함수를 사용할 것
use bfs::{extract_all_paths_with_end_points, visualize_paths, Point, load_skeleton_from_png};

fn main() {
    // # 추정: 예시용 스켈레톤 (한 줄짜리 선형 크랙)
    // 1행 15열, 전부 1인 스켈레톤
        // 1) PNG에서 스켈레톤 로드
        let skeleton: Vec<Vec<u8>> =
        load_skeleton_from_png("./skeleton.png", 128).expect("스켈레톤 로드 실패");

    // 끝점 두 개: 왼쪽 끝 (0,0), 오른쪽 끝 (14,0)
    let end_points: Vec<Point> = vec![(0, 0), (14, 0)];

    let paths = extract_all_paths_with_end_points(&skeleton, end_points);

    println!("경로 개수: {}", paths.len());
    for (i, path) in paths.iter().enumerate() {
        println!("경로 {} 길이: {}", i, path.len());
        println!("경로 {} 좌표: {:?}", i, path);
    }

        // ============== 시각화 추가 ==============
        let height = skeleton.len() as u32;
        let width = skeleton[0].len() as u32;
    
        visualize_paths(&paths, width, height, "cracks.png")
            .expect("시각화 저장 실패");
    
        println!(">> cracks.png 파일로 시각화 저장됨");
}

